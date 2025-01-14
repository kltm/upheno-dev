import yaml
import os
import pandas as pd
from subprocess import check_call

class uPhenoConfig:
    def __init__(self, config_file):
        self.config = yaml.load(open(config_file, 'r'))

    def get_download_location(self, id):
        return [t['mirror_from'] for t in self.config.get("sources") if t['id'] == id][0]

    def get_source_ids(self):
        return [t['id'] for t in self.config.get("sources")]

    def get_anatomy_dependency(self, id):
        return [t['anatomy'] for t in self.config.get("sources") if t['id'] == id][0]

    def get_file_location(self, id):
        return [t['file_path'] for t in self.config.get("sources") if t['id'] == id][0]

    def get_phenotype_ontologies(self):
        return self.config.get("species_modules")
        
    def get_upheno_intermediate_layer_depth(self):
        return int(self.config.get("upheno_intermediate_layer_depth"))
    
    def get_remove_disjoints(self):
        return self.config.get("remove_disjoints")
        
    def get_blacklisted_upheno_ids(self):
        return self.config.get("blacklisted_upheno_iris")

    def get_upheno_axiom_blacklist(self):
        return self.config.get("upheno_axiom_blacklist")

    def get_dependencies(self, id):
        dependencies = []
        dependencies.extend(self.config.get("common_dependencies"))
        try:
            odeps = [t['dependencies'] for t in self.config.get("sources") if t['id'] == id][0]
            dependencies.extend(odeps)
        except:
            print("No dependencies for "+id)

        return dependencies

    def get_taxon_label(self, id):
        return [t['taxon_label'] for t in self.config.get("sources") if t['id'] == id][0]

    def get_taxon(self, id):
        return [t['taxon'] for t in self.config.get("sources") if t['id'] == id][0]

    def get_prefix_iri(self, id):
        return [t['prefix_iri'] for t in self.config.get("sources") if t['id'] == id][0]

    def get_root_phenotype(self, id):
        return [t['root'] for t in self.config.get("sources") if t['id'] == id][0]

    def get_xref_alignments(self, id):
        alignments = []
        try:
            odeps = [t['xref_alignments'] for t in self.config.get("sources") if t['id'] == id][0]
            alignments.extend(odeps)
        except:
            print("No xref alignments for "+id)

        return alignments


    def is_clean_dir(self):
        return self.config.get("clean")

    def is_overwrite_matches(self):
        return self.config.get("overwrite_matches")

    def is_overwrite_ontologies(self):
        return self.config.get("overwrite_ontologies")

    def is_match_owl_thing(self):
        return self.config.get("match_owl_thing")

    def is_skip_pattern_download(self):
        return self.config.get("skip_pattern_download")

    def is_overwrite_upheno_intermediate(self):
        return self.config.get("overwrite_upheno_intermediate")

    def is_allow_non_upheno_eq(self):
        return self.config.get("allow_non_upheno_eq")

    def is_inferred_class_hierarchy(self, id):
        return [('class_hierarchy' in t and t['class_hierarchy'] != "asserted") for t in self.config.get("sources") if t['id'] == id][0]

    def get_external_timeout(self):
        return str(self.config.get("timeout_external_processes"))

    def get_max_upheno_id(self):
        return int(self.config.get("max_upheno_id"))

    def get_min_upheno_id(self):
        return int(self.config.get("min_upheno_id"))

    def get_pattern_repos(self):
        return self.config.get("pattern_repos")

    def get_working_directory(self):
        return self.config.get("working_directory")

    def get_robot_opts(self):
        return self.config.get("robot_opts")

    def get_legal_fillers(self):
        return self.config.get("legal_fillers")

    def get_upheno_profiles(self):
        return [t['id'] for t in self.config.get("upheno_profiles")]

    def get_upheno_profile_components(self,id):
        return [t['species_modules'] for t in self.config.get("upheno_profiles") if t['id'] == id][0]

    def get_instantiate_superclasses_pattern_vars(self):
        return self.config.get("instantiate_superclasses_pattern_vars")

    def get_robot_java_args(self):
        return self.config.get("robot_java_args")

    def get_taxon_restriction_table(self, ids):
        return [[t['root'],t['taxon'],t['taxon_label'],t['modifier']] for t in self.config.get("sources") if t['id'] in ids]

    def set_path_for_ontology(self, id, path):
        for t in self.config.get("sources"):
            if t['id'] == id:
                t['file_path'] = path


def cdir(path):
    if not os.path.exists(path):
        os.makedirs(path)

# ROBOT wrappers
def robot_extract_seed(ontology_path,seedfile,sparql_terms, TIMEOUT="60m", robot_opts="-v"):
    print("Extracting seed of "+ontology_path+" with "+sparql_terms)
    try:
        check_call(['timeout','-t',TIMEOUT,'robot', 'query',robot_opts,'--use-graphs','true','-f','csv','-i', ontology_path,'--query', sparql_terms, seedfile])
    except Exception as e:
        print(e.output)
        raise Exception("Seed extraction of" + ontology_path + " failed")

def robot_extract_module(ontology_path,seedfile, ontology_merged_path, TIMEOUT="60m", robot_opts="-v"):
    print("Extracting module of "+ontology_path+" to "+ontology_merged_path)
    try:
        check_call(['timeout','-t',TIMEOUT,'robot', 'extract',robot_opts,'-i', ontology_path,'-T', seedfile,'--method','BOT', '--output', ontology_merged_path])
    except Exception as e:
        print(e.output)
        raise Exception("Module extraction of " + ontology_path + " failed")

def robot_dump_disjoints(ontology_path,term_file, ontology_removed_path, TIMEOUT="60m", robot_opts="-v"):
    print("Removing disjoint class axioms from "+ontology_path+" and saving to "+ontology_removed_path)
    try:
        check_call(['timeout','-t',TIMEOUT,'robot', 'remove',robot_opts,'-i', ontology_path,'--term-file',term_file,'--axioms','disjoint', '--output', ontology_removed_path])
    except Exception as e:
        print(e.output)
        raise Exception("Removing disjoint class axioms from " + ontology_path + " failed")

def robot_remove_mentions_of_nothing(ontology_path, ontology_removed_path, TIMEOUT="3600", robot_opts="-v"):
    print("Removing mentions of nothing from "+ontology_path+" and saving to "+ontology_removed_path)
    try:
        check_call(['timeout','-t',TIMEOUT,'robot', 'remove',robot_opts,'-i', ontology_path,'--term','http://www.w3.org/2002/07/owl#Nothing', '--axioms','logical','--preserve-structure', 'false', '--output', ontology_removed_path])
    except Exception as e:
        print(e.output)
        raise Exception("Removing mentions of nothing from " + ontology_path + " failed")

def robot_remove_upheno_blacklist_and_classify(ontology_path, ontology_removed_path, blacklist_ontology, TIMEOUT="3600", robot_opts="-v"):
    print("Removing upheno blacklist axioms from "+ontology_path+" and saving to "+ontology_removed_path)
    try:
        check_call(['timeout','-t',TIMEOUT,'robot', 'merge',robot_opts,'-i', ontology_path,'unmerge', '-i', blacklist_ontology,'reason', '--reasoner','ELK', '--output', ontology_removed_path])
    except Exception as e:
        print(e.output)
        raise Exception("Removing mentions of nothing from " + ontology_path + " failed")

def robot_merge(ontology_list, ontology_merged_path, TIMEOUT="3600", robot_opts="-v"):
    print("Merging " + str(ontology_list) + " to " + ontology_merged_path)
    try:
        callstring = ['timeout','-t', TIMEOUT, 'robot', 'merge', robot_opts]
        merge = " ".join(["--input " + s for s in ontology_list]).split(" ")
        callstring.extend(merge)
        callstring.extend(['--output', ontology_merged_path])
        check_call(callstring)
    except Exception as e:
        print(e)
        raise Exception("Merging of" + str(ontology_list) + " failed")

def robot_prepare_ontology_for_dosdp(o, ontology_merged_path,sparql_terms_class_hierarchy, TIMEOUT="3600", robot_opts="-v"):
    print("Preparing " + str(o) + " for DOSDP: " + ontology_merged_path)
    subclass_hierarchy = os.path.join(os.path.dirname(ontology_merged_path),"class_hierarchy_"+os.path.basename(ontology_merged_path))
    subclass_hierarchy_seed = os.path.join(os.path.dirname(ontology_merged_path),
                                      "class_hierarchy_seed_" + os.path.basename(ontology_merged_path))
    robot_extract_seed(o, subclass_hierarchy_seed, sparql_terms_class_hierarchy, TIMEOUT, robot_opts)
    robot_class_hierarchy(o,subclass_hierarchy_seed,subclass_hierarchy,REASON=True,TIMEOUT=TIMEOUT,robot_opts=robot_opts)
    try:
        callstring = ['timeout','-t', TIMEOUT, 'robot', 'merge', robot_opts,"-i",o]
        callstring.extend(['remove','--term', 'rdfs:label', '--select', 'complement', '--select', 'annotation-properties', '--preserve-structure', 'false'])
        callstring.extend(['--output', ontology_merged_path])
        check_call(callstring)
    except Exception as e:
        print(e)
        raise Exception("Preparing " + str(o) + " for DOSDP: " + ontology_merged_path + " failed")

def robot_upheno_release(ontology_list, ontology_merged_path, name, TIMEOUT="3600", robot_opts="-v"):
    print("Finalising  " + str(ontology_list) + " to " + ontology_merged_path+", "+name)
    try:
        callstring = ['timeout','-t', TIMEOUT, 'robot', 'merge', robot_opts]
        merge = " ".join(["--input " + s for s in ontology_list]).split(" ")
        callstring.extend(merge)
        callstring.extend(['remove', '--axioms', 'disjoint', '--preserve-structure', 'false'])
        callstring.extend(['remove', '--term','http://www.w3.org/2002/07/owl#Nothing', '--axioms','logical','--preserve-structure', 'false'])
        callstring.extend(['reason','--reasoner','ELK','reduce','--reasoner','ELK'])
        callstring.extend(['--output', ontology_merged_path])
        check_call(callstring)
    except Exception as e:
        print(e)
        raise Exception("Finalising " + str(ontology_list) + " failed...")

def robot_upheno_component(component_file,remove_eqs, TIMEOUT="3600", robot_opts="-v"):
    #robot remove --axioms "disjoint" --preserve-structure false reason --reasoner ELK -o /data/upheno_pre-fixed_mp-hp.owl
    print("Preparing uPheno component  " + str(component_file))
    try:
        callstring = ['timeout','-t', TIMEOUT, 'robot', 'merge','-i',component_file]
        callstring.extend(['remove','-T',remove_eqs,'--axioms','equivalent','--preserve-structure','false'])
        callstring.extend(['--output', component_file])
        check_call(callstring)
    except Exception as e:
        print(e)
        raise Exception("Preparing uPheno component " + str(component_file) + " failed...")

def robot_children_list(o,query,outfile,TIMEOUT="3600",robot_opts="-v"):
    print("Extracting children from  " + str(o) +" using "+str(query))
    try:
        check_call(['timeout','-t',TIMEOUT,'robot', 'query',robot_opts,'--use-graphs','true','-f','csv','-i', o,'--query', query, outfile])

    except Exception as e:
        print(e)
        raise Exception("Preparing uPheno component " + str(o) + " failed...")


def robot_class_hierarchy(ontology_in_path, class_hierarchy_seed, ontology_out_path, REASON = True , TIMEOUT="3600", robot_opts="-v"):
    print("Extracting class hierarchy from " + str(ontology_in_path) + " to " + ontology_out_path + "(Reason: "+str(REASON)+")")
    try:
        callstring = ['timeout','-t', TIMEOUT, 'robot', 'merge', robot_opts,"--input",ontology_in_path]
        if REASON:
            callstring.extend(['reason','--reasoner','ELK'])

        callstring.extend(['filter','-T',class_hierarchy_seed,'--axioms','subclass','--preserve-structure','false','--trim','false','--output', ontology_out_path])
        check_call(callstring)
    except Exception as e:
        print(e)
        raise Exception("Extracting class hierarchy from " + str(ontology_in_path) + " to " + ontology_out_path + " failed")


def dosdp_generate(pattern,tsv,outfile, RESTRICT_LOGICAL=False,TIMEOUT="3600",ONTOLOGY=None):
    try:
        callstring = ['timeout','-t', TIMEOUT, 'dosdp-tools', 'generate', '--infile=' + tsv, '--template=' + pattern,
             '--obo-prefixes=true']
        if RESTRICT_LOGICAL:
            callstring.extend(['--restrict-axioms-to=logical'])
        if ONTOLOGY is not None:
            callstring.extend(['--ontology='+ONTOLOGY])
        callstring.extend(['--outfile=' + outfile])
        check_call(callstring)
    except:
        raise Exception("Pattern generation failed: "+pattern+", "+tsv+", "+outfile+".")


def dosdp_extract_pattern_seed(tsv_files,seedfile):
    classes = []
    try:
        for tsv in tsv_files:
            df = pd.read_csv(tsv, sep='\t')
            classes.extend(df['defined_class'])
        with open(seedfile, 'w') as f:
            for item in list(set(classes)):
                f.write("%s\n" % item)
    except Exception as e:
        print(e)
        raise Exception("Extracting seed from all TSV files failed..")

def write_list_to_file(file_path,list):
    with open(file_path, 'w') as f:
        for item in list:
            f.write("%s\n" % item)

def touch(path):
    with open(path, 'a'):
        os.utime(path, None)

def rm(path):
    if os.path.isfile(path):
        os.remove(path)
    else:  ## Show an error ##
        print("Error: %s file not found" % path)