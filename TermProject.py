from thymeml import * # THYME-ML object model
from os import listdir # Directory
from os.path import isfile, join # Directory
import codecs # Reading file with utf-8 encoding

def contentsOfFile(filename):
    file = codecs.open(filename, "r", "utf-8")
    content = file.read()
    return content
    
def printSectionDivider(depth):
    if depth == 0:
        print "________________________________________"
    elif depth == 1:
        print "\t----------------------" 
    elif depth == 2:
        print "\t\t------------------" 

def processDocumentThymeMLData(data):

    print "\tProcessing Data..."
    printSectionDivider(0)

    # Events
    entities = [a for a in data.annotations if type(a) is ThymeMLEntity]
    if len([a for a in entities if a.type == "DOCTIME"]) < 1:
        print "ERROR: Found LESS than 1 DOCTIME entity annotation"
    elif len([a for a in entities if a.type == "DOCTIME"]) > 1:
        print "ERROR: Found MORE than 1 DOCTIME entity annotation"
    docTime = [a for a in entities if a.type == "DOCTIME"][0] # There should be exactly one match
    events = [a for a in entities if a.type == "EVENT"]
    timex3s = [a for a in entities if a.type == "TIMEX3"]
    markables = [a for a in entities if a.type == "Markable"]

    print "\tENTITY ANNOTATIONS (Total: " + str(len(entities)) + ")"
    printSectionDivider(2)
    print "\t\tMarkables (" + str(len(markables)) + ")"
    for annotation in markables:
        print "" #annotation.spansContent
    printSectionDivider(2)
    print "\t\tDocTime (" + str(docTime.spansContent) 
    printSectionDivider(2)
    print "\t\tEvents (" + str(len(events)) + ")"
    for annotation in events:
        print "" #annotation.spansContent
    printSectionDivider(2)
    print "\t\tTIMEX3s (" + str(len(timex3s)) + ")"
    for annotation in timex3s:
        print "" #annotation.spansContent
    printSectionDivider(2)

    # Relations
    relations = [a for a in data.annotations if type(a) is ThymeMLRelation]
    identicalRelations = [r for r in data.annotations if r.type == "Identical"]
    
    # TLINKs connect two EVENTs, or an EVENT and a TIMEX3 together, specifying the temporal relationship between them (before, overlap, contains, begins-on and ends-on)
    tlinkRelations = [r for r in data.annotations if r.type == "TLINK"]
    alinkRelations = [r for r in data.annotations if r.type == "ALINK"]
    print "\tRELATION ANNOTATIONS (Total: " + str(len(relations)) + ")"
    printSectionDivider(2)
    print "\t\tTLINK Relations (" + str(len(tlinkRelations)) + ")"
    for annotation in tlinkRelations:
        if type(annotation) is ThymeMLRelation: 
            print "" #annotation.spansContent

    printSectionDivider(2)
    print "\t\tALINK Relations (" + str(len(alinkRelations)) + ")"
    for annotation in alinkRelations:
        if type(annotation) is ThymeMLRelation: 
            print "" #annotation.spansContent

    printSectionDivider(2)
    print "\t\tIdentical Relations (" + str(len(identicalRelations)) + ")"
    for annotation in identicalRelations:
        if type(annotation) is ThymeMLRelation: 
            print "" #annotation.spansContent

    printSectionDivider(0)
    print "Checking coreference chains (Identical) for multiple types..."
    
    for relation in identicalRelations:
        hasMarkable = False
        hasEvent = False
        hasTimex3 = False
        for reference in relation.allReferences:
            if reference.type == "Markable":
                hasMarkable = True
            elif reference.type == "EVENT":
                hasEvent = True
            elif reference.type == "TIMEX3":
                hasTimex3 = True
        if (hasMarkable + hasEvent + hasTimex3) > 1:
            printSectionDivider(1)
            print "\tCoreference chain with multiple types:"
            for reference in relation.allReferences:
                print "\t\t" + reference.type + ": " + str(reference.spansContent)
        

    printSectionDivider(0)
    print "Replacing TLINK/ALINK relationship source/target entities with the coreference chain relation they belong to (if any)"
    
    print "TLINK Relations"
    mergeCoreferentEventsInTemporalRelations(tlinkRelations, identicalRelations)
    print "ALINK Relations"
    mergeCoreferentEventsInTemporalRelations(alinkRelations, identicalRelations)

def mergeCoreferentEventsInTemporalRelations(temporalRelations, coreferenceChains):

    replaced = 0
    total = 0

    for temporalRelation in temporalRelations:

        for coreferenceChain in coreferenceChains:

            references = coreferenceChain.allReferences

            # Source
            if temporalRelation.properties["Source"] in references:
                # print "Found TLINK relation with Source belonging to a coreference chain relation"
                temporalRelation.properties["Source"] = coreferenceChain
                replaced += 1

            # Target
            if temporalRelation.properties["Target"] in references:
                # print "Found TLINK relation with Target belonging to a coreference chain relation"
                temporalRelation.properties["Target"] = coreferenceChain
                replaced += 1

    print "\tTemporal Relation Components Replaced with Coreference Chains " + str(replaced) + "/" + str(len(temporalRelations)*2)

# Convert XML to Python objects (either specialized classes or dictionary)
def main():

    documentDirectory = "./Tim-Round1/THYME-Analysis/"
    xmlDirectory = "./Tim-Round2/thyme2mergedfiles/";
    
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

    printSectionDivider(0)
    print "Generating THYME data model for each document and XML pair"
    for i, folder in enumerate(clinicFolders): # Tim confirmed that currently we are not doing cross-document annotation
    
        # e.g. ID001_clinic_001

        documentName = folder # document name is same as folder
        documentPath = documentDirectory + folder + "/" + documentName
        print "\tDocument: " + documentPath

        documentContents = contentsOfFile(documentPath)

        print "\t\tNumber of Lines: " + str(documentContents.count('\n'))
        print "\t\tNumber of Characters: " + str(len(documentContents))

        xmlPath = xmlDirectory + folder + "/" + documentName + ".Thyme2v1-withindoc.ogormant.inprogress.xml"
        
        print "\tXML: " + xmlPath

        printSectionDivider(0)
        print "\tReading Files..."
        printSectionDivider(0)
        data = ThymeMLData.from_file(xmlPath, documentContents)
        processDocumentThymeMLData(data)
        
        break; # For now just process the first document

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