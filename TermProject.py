import os
import sys
import gc
from os import listdir # Directory
from os.path import isfile, join # Directory
import codecs # Reading file with utf-8 encoding
from DocumentProcessor import *

def contentsOfFile(filename):
    file = codecs.open(filename, "r", "utf-8")
    content = file.read()
    return content

# Convert XML to Python objects (either specialized classes or dictionary)
def main():

    documentDirectory = "./Tim-Round1/THYME-Analysis/"
    xmlDirectory = "./Tim-Round2/thyme2mergedfiles/"
    outputDirectory = "./output/"
    
    allFolders = [f for f in listdir(xmlDirectory) if not isfile(join(xmlDirectory, f))]
    # onlyfiles = [f for f in os.listdir(currentDir) if os.path.isfile(join(currentDir, f))]
    
    print "XML Directory: " + xmlDirectory
    print "\tFound " + str(len(allFolders)) + " Folders"

    clinicFolders = []
    for folder in allFolders:
        if "_path_" not in folder:
            clinicFolders.append(folder) # filter out folder like "ID001_path_002"

    print "\tFound " + str(len(clinicFolders)) + " Clinic Folders"

    print "Document Root Directory: " + documentDirectory

    print "Generating THYME data model for each document and XML pair"
    print "Output directory: " + outputDirectory

    orig_stdout = sys.stdout

    temporalClosureConflictTotalCount = 0
    identityCoreferenceResolutionConflictTotalCount = 0
    selfReferentialTemporalRelationTotalCount = 0
    for i, folder in enumerate(clinicFolders): # Tim confirmed that currently we are not doing cross-document annotation

        sys.stdout = orig_stdout

        documentName = folder # document name is same as folder, e.g. ID001_clinic_001
        documentPath = documentDirectory + folder + "/" + documentName

        # if documentName not in ["ID014_clinic_042", "ID023_clinic_067", "ID025_clinic_075", "ID067_clinic_197"]:
        #     continue

        outputPath = outputDirectory + documentName + "-processed.txt"
        print "\tProcessing " + documentName + " (" + str(i + 1) + " of " + str(len(clinicFolders)) + ")"
            
        if os.path.isfile(outputPath): # Don't process documents that already have generated output files
            continue

        dir = os.path.dirname(outputPath)
        if not os.path.exists(dir):
            os.makedirs(dir)

        f = file(outputPath, 'w')
        sys.stdout = f

        f = open(outputPath, 'w')
        print "Document: " + documentPath

        documentContents = contentsOfFile(documentPath)

        print "\tNumber of Lines: " + str(documentContents.count('\n'))
        print "\tNumber of Characters: " + str(len(documentContents))

        xmlPath = xmlDirectory + folder + "/" + documentName + ".Thyme2v1-withindoc.ogormant.inprogress.xml"
        
        print "\tXML: " + xmlPath

        (temporalClosureConflictCount, identityCoreferenceResolutionConflictCount, selfReferentialTemporalRelationCount) = processDocumentThymeMLData(xmlPath, documentName, documentContents)
        temporalClosureConflictTotalCount += temporalClosureConflictCount
        identityCoreferenceResolutionConflictTotalCount += identityCoreferenceResolutionConflictCount
        selfReferentialTemporalRelationTotalCount += selfReferentialTemporalRelationCount
        
        xmlPath = None
        data = None
        _XMLWrapper = None
        documentContents = None
        
        f.close()
        
        gc.collect()

    sys.stdout = orig_stdout
    print "Done with processing all documents"

    totalConflictCount = temporalClosureConflictTotalCount + identityCoreferenceResolutionConflictTotalCount + selfReferentialTemporalRelationTotalCount

    printSectionDivider(1)
    print "Root Causes of Temporal Inconsistencies"
    print ""
    if totalConflictCount > 0:
        print "Temporal Closure\t\t\t\t\t" + str(temporalClosureConflictTotalCount) + "/" + str(totalConflictCount) + "\t(" + str(100*temporalClosureConflictTotalCount/totalConflictCount) + "%)"
        print "Identity-Coreference Chain Resolution\t\t\t" + str(identityCoreferenceResolutionConflictTotalCount + selfReferentialTemporalRelationTotalCount) + "/" + str(totalConflictCount) + "\t(" + str(100*(identityCoreferenceResolutionConflictTotalCount + selfReferentialTemporalRelationTotalCount)/totalConflictCount) + "%)"
        print "\tSelf-Referential Relations\t\t\t" + str(selfReferentialTemporalRelationTotalCount) + "/" + str(totalConflictCount) + "\t|----(" + str(100*selfReferentialTemporalRelationTotalCount/totalConflictCount) + "%)"
        print "\tRelation Conflicts\t\t\t\t" + str(identityCoreferenceResolutionConflictTotalCount) + "/" + str(totalConflictCount) + "\t|----(" + str(100*identityCoreferenceResolutionConflictTotalCount/totalConflictCount) + "%)"
    else:
        print "No temporal inconsistencies found"

print "Starting..."
main()

'''
def mergeCoreference():

	Use entity id if not in any of these coreference chains.
	Warning: when doing find-replace, make sure to include angle brackets... so not replacing substrings.

	Use relations with "Identical" type to merge id's

	[DONE] Ignore documents with "_path_" in the name

	TLINK is the actual temporal relations
	ALINK - temporal relation for X that start or end Y
		X is a point at the start of Y (INITIATES)
		X is a point at the end of Y (TERMINATES)
}

def propagateRelations() {

	Instantiate indirect relations... If A < B and B < C then A < C

    findRelationConflicts()
	a) Look to see if C > A already exists. AKA Look to see if there are conflicts in the implicit event relations
}

# Create timeline...

# A test/study is always an event. The pathology repots might say something like, "MRI showed tumor". Things like tumor ("discovering the tumor") are considered implicit events.
# The annotators explicitly marked a tlink relation CONTAINS between MRI and "discovery of tumor". One fix for this would be to create/use a "CONTAINS.DISCOVERYOF" relation for these instances.
# Look for annotations that in are part/whole relations, and then look to see if those are also in tlinks.
# Kinds of part/whole relation
    # entity - entity
    # event - event
    # Everytime we see a part/whole relation, change the relationship type from "<type>Whole/Part</type>" to "<type>Event/Subevent</type>"
    # Then... look for instances of entity - event that are in a part/whole relation. In the corefernece relation, that
    # How did Tim do his merge?  

def findRelationConflicts() {
    
    var conflictingRelationPairs = []
    for relation1 in relations {
        for relation2 in relations {
            if relation1 == relation2 {
                continue;
            }
            
            if(relation1.doesConflict(relation2)) {
                conflictingRelationPairs.add([relation1, relation2])
            }
        }
    }
}

class Entity {
    
    var relations: [Relation]
}

class RelationProperties {

    // <type>TLINK</type> <parentsType>TemporalRelations</parentsType>
    var source: Entity // e.g. 762@e@ID012_clinic_034@gold 
    var type: String // e.g. CONTAINS
    var target: Entity // e.g. <Target>795@e@ID012_clinic_034@gold</Target>

    // <type>Identical</type> <parentsType>CorefChains</parentsType>
    var firstInstance: Entity // e.g. 295@e@ID012_clinic_034@gold
    var coreferring_Strings: [String] // [296@e@ID012_clinic_034@gold, 448@e@ID012_clinic_034@gold, 648@e@ID012_clinic_034@gold]
}

class Relation {
    
    var identifier: String // e.g. 2@r@ID012_clinic_034@gold
    var type: String // e.g. TLINK
    var parentsType: String // e.g. TemporalRelations
    var properties: RelationProperties

    var firstComponent: Entity
    var secondComponent: Entity
    var relationType // TLINK: "CONTAINS", "TERMINATES", "BEFORE", "INITIATES", "OVERLAP", "BEGINS-ON"
    // ALINK: CONTINUES, TERMINATES, INITIATES

    def doesConflict(otherRelation: Relation) -> Bool {

        bool relevantRelation = false;
        bool reversedRelation = false;
        // Enumerate types of conflicts
        if(self.firstComponent == otherRelation.firstComponent &&
           self.secondComponent == otherRelation.secondComponent) {
            relevantRelation = true;
        } else if(self.firstComponent == otherRelation.secondComponent &&
           self.secondComponent == otherRelation.firstComponent) {
            relevantRelation = true;
            reversedRelation = true;
        }

        if(!relevantRelation) {
            return false;
        }

        if(reversedRelation) {
            if(self.relationType == otherRelation.relationType) {
                return true;
            }
        } else {
            if(self.relationType != otherRelation.relationType) {
                return true;
            }
        }
    }
}
'''