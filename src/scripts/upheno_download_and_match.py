#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 8 14:24:37 2018

@author: Nicolas Matentzoglu
"""

import os, shutil, sys
import yaml
import urllib.request
import requests
import pandas as pd
from subprocess import check_call,CalledProcessError
from lib import uPhenoConfig, robot_extract_seed, robot_extract_module, robot_merge

### Configuration

upheno_config_file = sys.argv[1]
#upheno_config_file = os.path.join("/ws/upheno-dev/src/curation/upheno-config.yaml")
upheno_config = uPhenoConfig(upheno_config_file)
os.environ['ROBOT_JAVA_ARGS'] = upheno_config.get_robot_java_args()

TIMEOUT=upheno_config.get_external_timeout()
ws = upheno_config.get_working_directory()
robot_opts=upheno_config.get_robot_opts()


pattern_dir = os.path.join(ws,"curation/patterns-for-matching/")
ontology_for_matching_dir = os.path.join(ws,"curation/ontologies-for-matching/")
matches_dir = os.path.join(ws,"curation/pattern-matches/")
module_dir = os.path.join(ws,"curation/tmp/")

sparql_dir = os.path.join(ws,"sparql/")
xref_pattern = os.path.join(ws,"patterns/dosdp-patterns/xrefToSubClass.yaml")
sparql_terms = os.path.join(sparql_dir, "terms.sparql")

### Configuration end

### Methods
##

# This function interprets xref as subclass axioms (A xref B, A subclass B), use sparingly
def robot_xrefs(oid, mapto, mapping_file):
    global TIMEOUT, xref_pattern, robot_opts, upheno_config, module_dir
    sparql_xrefs = os.path.join(sparql_dir, "%s_xrefs.sparql" % mapto)
    print(oid)
    print(mapto)
    ontology_path = upheno_config.get_file_location(oid)
    xref_table = os.path.join(module_dir, oid + ".tsv")

    try:
        # Extracting xrefs from ontology to table
        check_call(['gtimeout', TIMEOUT, 'robot', 'query', robot_opts, '--use-graphs', 'true', '-f', 'tsv', '--input',
                    ontology_path, '--query', sparql_xrefs, xref_table])

        # Doing a bit of preprocessing on the SPARQL result: renaming columns, removing <> signs
        try:
            df = pd.read_csv(xref_table, sep='\t')
            df = df.rename(columns={'?defined_class': 'defined_class', '?xref': 'xref'})
            df['defined_class'] = df['defined_class'].str.replace('<', '')
            df['defined_class'] = df['defined_class'].str.replace('>', '')
            df['xref'] = df['xref'].str.replace('<', '')
            df['xref'] = df['xref'].str.replace('>', '')
            df.to_csv(xref_table, sep='\t', index=False)
        except pd.io.common.EmptyDataError:
            print(xref_table, " is empty and has been skipped.")

        # DOSDP generate the xrefs as subsumptions
        check_call(['gtimeout', TIMEOUT, 'dosdp-tools','generate','--infile='+xref_table,'--template='+xref_pattern,'--obo-prefixes=true','--restrict-axioms-to=logical','--outfile='+mapping_file])
    except Exception as e:
        print(e.output)
        raise Exception("Xref generation of" + ontology_path + " failed")

    return mapping_file

def robot_convert_merge(ontology_url, ontology_merged_path):
    print("Convert/Merging "+ontology_url+" to "+ontology_merged_path)
    global TIMEOUT, robot_opts
    try:
        check_call(['gtimeout',TIMEOUT,'robot', 'merge',robot_opts,'-I', ontology_url,'convert', '--output', ontology_merged_path])
    except Exception as e:
        print(e.output)
        raise Exception("Loading " + ontology_url + " failed")

def get_files_of_type_from_github_repo_dir(q,type):
    gh = "https://api.github.com/repos/"
    print(q)
    #contents = urllib.request.urlopen().read()
    url = gh+q
    f = requests.get(url)
    contents = f.text
    raw = yaml.load(contents)
    tsvs = []
    for e in raw:
        tsv = e['name']
        if tsv.endswith(type):
            tsvs.append(e['download_url'])
    return tsvs

def get_all_tsv_urls(tsvs_repos):
    tsvs = []

    for repo in tsvs_repos:
        ts = get_files_of_type_from_github_repo_dir(repo,'.tsv')
        tsvs.extend(ts)

    tsvs_set = set(tsvs)
    return tsvs_set

def get_upheno_pattern_urls(upheno_pattern_repo):
    upheno_patterns = get_files_of_type_from_github_repo_dir(upheno_pattern_repo,'.yaml')
    return upheno_patterns

def export_yaml(data,fn):
    with open(fn, 'w') as outfile:
        yaml.dump(data, outfile, default_flow_style=False)

def get_pattern_urls(upheno_pattern_repo):
    upheno_patterns = []
    for location in upheno_pattern_repo:
        upheno_patterns.extend(get_upheno_pattern_urls(location))
    return upheno_patterns

def download_patterns(upheno_pattern_repo, pattern_dir):
    upheno_patterns = get_pattern_urls(upheno_pattern_repo)
    filenames = []
    for url in upheno_patterns:
        a = urllib.parse.urlparse(url)
        filename = os.path.join(pattern_dir,os.path.basename(a.path))
        #urllib.request.urlretrieve(url, filename)
        filenames.append(filename)
    return filenames

def prepare_phenotype_ontologies_for_matching(overwrite=True):
    global upheno_config, sparql_terms, ontology_for_matching_dir, TIMEOUT, robot_opts
    for id in upheno_config.get_phenotype_ontologies():
        print("Preparing %s" %id)
        filename = upheno_config.get_file_location(id)
        imports = []
        for dependency in upheno_config.get_dependencies(id):
            print("Dependency: "+dependency)
            imports.append(upheno_config.get_file_location(dependency))
        merged = os.path.join(module_dir, id + '-allimports-merged.owl')
        module = os.path.join(module_dir, id + '-allimports-module.owl')
        merged_pheno = os.path.join(ontology_for_matching_dir, id + '.owl')
        seed = os.path.join(module_dir, id + '_seed.txt')
        if overwrite or not os.path.exists(module):
            robot_extract_seed(filename, seed, sparql_terms, TIMEOUT, robot_opts)
            robot_merge(imports, merged, TIMEOUT, robot_opts)
            robot_extract_module(merged, seed, module, TIMEOUT, robot_opts)
        if overwrite or not os.path.exists(merged_pheno):
            ontology_for_matching = [module, filename]
            robot_merge(ontology_for_matching, merged_pheno, TIMEOUT, robot_opts)
    return upheno_config

def match_patterns(upheno_config,pattern_files,matches_dir, overwrite=True):
    for pattern_path in pattern_files:
        for id in upheno_config.get_phenotype_ontologies():
            ontology_path = os.path.join(ontology_for_matching_dir,id+".owl")
            dosdp_pattern_match(ontology_path,pattern_path,matches_dir, overwrite)

def dosdp_pattern_match(ontology_path, pattern_path, matches_dir, overwrite=True):
    print("Matching " + ontology_path + " to " + pattern_path)
    global TIMEOUT
    try:
        oid = os.path.basename(ontology_path).replace(".owl","")
        pid = os.path.basename(pattern_path).replace(".yaml", ".tsv")
        outdir = os.path.join(matches_dir,oid)
        if not os.path.exists(outdir):
            os.makedirs(outdir)
        out_tsv = os.path.join(outdir,pid)
        if overwrite or not os.path.exists(out_tsv):
            check_call(['gtimeout', TIMEOUT, 'dosdp-tools', 'query', '--ontology='+ontology_path, '--reasoner=elk', '--obo-prefixes=true', '--template='+pattern_path,'--outfile='+out_tsv])
        else:
            print("Match already made, bypassing.")
    except CalledProcessError as e:
        print(e.output)

def list_files(directory, extension):
    return (f for f in os.listdir(directory) if f.endswith('.' + extension))

def download_sources(dir,overwrite=True):
    global upheno_config
    for oid in upheno_config.get_source_ids():
        filename = os.path.join(dir,oid+".owl")
        url = upheno_config.get_download_location(oid)
        if url not in ['xref']:
            if overwrite or not os.path.exists(filename):
                robot_convert_merge(url, filename)
            print("%s downloaded successfully." % filename)
            upheno_config.set_path_for_ontology(oid, filename)
    for oid in upheno_config.get_source_ids():
        filename = os.path.join(dir, oid + ".owl")
        url = upheno_config.get_download_location(oid)
        if url in ['xref']:
            if overwrite or not os.path.exists(filename):
                id = oid.split("-")[0]
                xref = oid.split("-")[1]
                robot_xrefs(id, xref, filename)
            print("%s compiled successfully through xrefs." % filename)
            upheno_config.set_path_for_ontology(oid, filename)



### Methods end

if upheno_config.is_clean_dir():
    print("Cleanup..")
    shutil.rmtree(matches_dir)
    os.makedirs(matches_dir)
    shutil.rmtree(ontology_for_matching_dir)
    os.makedirs(ontology_for_matching_dir)
    shutil.rmtree(module_dir)
    os.makedirs(module_dir)


print('UNTIL THIS SSL ERROR IS FIXED, just index files in pattern dir rather than downloading..')
#pattern_files = download_patterns(upheno_pattern_repo, pattern_dir)
pattern_files = [os.path.join(pattern_dir,f) for f in os.listdir(pattern_dir) if os.path.isfile(os.path.join(pattern_dir, f)) and f.endswith('.yaml')]

download_sources(module_dir,upheno_config.is_overwrite_ontologies())

prepare_phenotype_ontologies_for_matching(upheno_config.is_overwrite_ontologies())

match_patterns(upheno_config,pattern_files, matches_dir, upheno_config.is_overwrite_matches())