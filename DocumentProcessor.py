from thymeml import * # THYME-ML object model

def printSectionDivider(depth):

    if depth == 0:
        print "########################################"
        print "########################################"
    elif depth == 1:
        print "________________________________________"
    elif depth == 2:
        print "\t----------------------" 
    elif depth == 3:
        print "\t\t------------------" 

def processDocumentThymeMLData(xmlPath, documentName, documentContents):

    data = ThymeMLData.from_file(xmlPath, documentContents)

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
    #printSectionDivider(3)
    print "\t\tMarkables (" + str(len(markables)) + ")"
    # for annotation in markables:
        # print "" #annotation.spansContent
    #printSectionDivider(3)
    print "\t\tDocTime (" + str(docTime.spansContent) 
    #printSectionDivider(3)
    print "\t\tEvents (" + str(len(events)) + ")"
    # for annotation in events:
        # print "" #annotation.spansContent
    #printSectionDivider(3)
    print "\t\tTIMEX3s (" + str(len(timex3s)) + ")"
    # for annotation in timex3s:
        # print "" #annotation.spansContent
    #printSectionDivider(3)

    # Relations
    relations = [a for a in data.annotations if type(a) is ThymeMLRelation]
    identicalRelations = [r for r in data.annotations if r.type == "Identical"]
    
    # TLINKs connect two EVENTs, or an EVENT and a TIMEX3 together, specifying the temporal relationship between them (before, overlap, contains, begins-on and ends-on)
    tlinkRelations = [r for r in data.annotations if r.type == "TLINK"]
    alinkRelations = [r for r in data.annotations if r.type == "ALINK"]
    print "\tRELATION ANNOTATIONS (Total: " + str(len(relations)) + ")"
    #printSectionDivider(3)
    print "\t\tTLINK Relations (" + str(len(tlinkRelations)) + ")"
    # for annotation in tlinkRelations:
    #     if type(annotation) is ThymeMLRelation: 
    #         print "" #annotation.spansContent

   #printSectionDivider(3)
    print "\t\tALINK Relations (" + str(len(alinkRelations)) + ")"
    # for annotation in alinkRelations:
    #     if type(annotation) is ThymeMLRelation: 
    #         print "" #annotation.spansContent

    #printSectionDivider(3)
    print "\t\tIdentical Relations (" + str(len(identicalRelations)) + ")"
    # for annotation in identicalRelations:
    #     if type(annotation) is ThymeMLRelation: 
    #         print "" #annotation.spansContent

    printSectionDivider(1)
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
            printSectionDivider(2)
            print "\tCoreference chain with multiple types:"
            for reference in relation.allReferences:
                print "\t\t" + reference.type + ": " + str(reference.spansContent)

    printSectionDivider(1)
    print "Confirm that all Identical Relations (" + str(len(identicalRelations)) + ") are mutually independent (do not share annotations)"
    independentIdenticalRelations = 0
    for relation in identicalRelations:
        for reference in relation.allReferences:
            for relation2 in identicalRelations:
                if relation is relation2:
                    continue
                if reference in relation2.allReferences:
                    independentIdenticalRelations += 1
    if independentIdenticalRelations > 0:
        print "\tERROR: Found (" + str(independentIdenticalRelations) + ")Identical relations with references in common!"
    else:
        print "\t All identical relations are independent."

    # printSectionDivider(1)
    # print "Confirm that all Events are anchored to the timeline (Whether this anchoring is as specific as a TLINK to a TIMEX3 or general as the DocTimeRel marking)..."
    # for event in events:
    #     if not event.isAnchored(relations):
    #         print "Event (" + event.text + ") is not anchored!!!"

    printSectionDivider(1)
    print "Replacing TLINK relationship source/target entities with the coreference chain relation they belong to (if any)"

    print "TLINK Relations"
    mergeCoreferentEventsInTemporalRelations(tlinkRelations, identicalRelations)
    # print "ALINK Relations" # We are no longer handling ALINK relations
    # mergeCoreferentEventsInTemporalRelations(alinkRelations, identicalRelations)

    printSectionDivider(1)
    print "Performing relation inferencing..."

    conflictingRelationPairs = []
    foundImplicitRelation = True
    implicitRelationCount = 0
    while foundImplicitRelation:
        foundImplicitRelation = False
        
        for relation1 in tlinkRelations:

            for relation2 in tlinkRelations:

                if relation1 is relation2:
                    continue

                allReferences = relation1.allReferences[:]
                allReferences.extend(relation2.allReferences)

                if len(allReferences) is not 4:
                    # print "ERROR: There should always be 4 annotations to compare when propogating relations. Found (" + str(len(allReferences)) + ")"
                    continue

                uniqueReferences = set(allReferences) # This did not work because of non-hashable lists
                # uniqueReferences = list()
                # for reference in allReferences:
                #     isUnique = True
                #     for uniqueReference in uniqueReferences:
                #         if uniqueReference.id == reference.id:
                #             isUnique = False
                #     if isUnique:
                #         uniqueReferences.append(reference)

                if len(uniqueReferences) == 2: # Complete overlap... look for conflicts (2 overlapping references)
                    
                    # print "\t\tChecking for conflict or agreement"

                    referenceAlignment = relation1.properties["Source"] is relation2.properties["Source"]  # x R1 y, x R2 y

                    relationConflict = False
                    if referenceAlignment:
                        relationConflict = relation1.properties["Type"] != relation2.properties["Type"]
                    else:
                        relationConflict = (relation1.properties["Type"] == "BEGINS-ON" and relation2.properties["Type"] == "ENDS-ON") or (relation2.properties["Type"] == "BEGINS-ON" and relation1.properties["Type"] == "ENDS-ON")                    

                    # Relation Conflict
                    if relationConflict:
                        relationPair = (relation1, relation2)
                        if relationPair not in conflictingRelationPairs:
                            conflictingRelationPairs.append(relationPair)

                elif len(uniqueReferences) == 3: # Create new explicit relation (1 overlapping reference)

                    '''
                    We use Allen's Transitivity Table for the Twelve Temporal Relations, except that
                    THYME Annotation Guidelines only support 5 different temporal relation TLINK types:
                        "BEFORE", "CONTAINS", "OVERLAP", "BEGINS-ON", "ENDS-ON"
                    Therefore we first do some magic to convert THYME TLINK types to Allen's relations
                    when the events are reversed, and then once the temporal closure is complete, we convert
                    Allen's relation types back to THYME relation types. In this way, we can support the following types:
                        "BEFORE", "AFTER", "DURING", "CONTAINS", "OVERLAP", "BEGINS-ON", "ENDS-ON"
                    Since THYME Annotation Guidelines merge Allen's "Overlaps" and "Overlapped-By" into a single type,
                    therefore we do not apply temporal closure to temporal relation TLINKs of type "OVERLAP"  
                    '''

                    # x R1 y, y R2 z # None reversed
                    newRelationType = ""
                    relation1Reversed = False
                    relation2Reversed = False
                    if relation1.properties["Source"] is relation2.properties["Source"]: # y R1 x, y R2 z # 1st reversed
                        relation1Reversed = True
                    elif relation1.properties["Target"] is relation2.properties["Target"]: # x R1 y, z R2 y # 2nd reversed
                        relation2Reversed = True
                    elif relation1.properties["Source"] is relation2.properties["Target"]: # y R1 x, z R2 y # 1st/2nd reversed
                        relation1Reversed = True
                        relation2Reversed = True

                    # Reverse the relation if necessary, since ThymeML does not use AFTER or DURING relations
                    relation1Resolved = relation1.properties["Type"]
                    if relation1.properties["Type"] == "BEFORE" and relation1Reversed:
                        relation1Resolved = "AFTER"
                    elif relation1.properties["Type"] == "CONTAINS" and relation1Reversed:
                        relation1Resolved = "DURING"

                    relation2Resolved = relation2.type
                    if relation2.properties["Type"] == "BEFORE" and relation2Reversed:
                        relation2Resolved = "AFTER"
                    elif relation2.properties["Type"] == "CONTAINS" and relation2Reversed:
                        relation2Resolved = "DURING"

                    # Temporal closure
                    if relation1Resolved == "BEFORE":
                        if relation2Resolved in ["BEFORE", "CONTAINS", "ENDS-ON"]:
                            newRelationType = "BEFORE"
                    if relation1Resolved == "AFTER":
                        if relation2Resolved in ["AFTER", "CONTAINS", "BEGINS-ON"]:
                            newRelationType = "AFTER"
                    if relation1Resolved == "DURING":
                        if relation2Resolved in ["BEFORE", "ENDS-ON"]:
                            newRelationType = "BEFORE"
                        elif relation2Resolved in ["AFTER", "BEGINS-ON"]:
                            newRelationType = "AFTER"
                        elif relation2Resolved in ["DURING"]:
                            newRelationType = "DURING"
                    elif relation1Resolved == "CONTAINS":
                        if relation2Resolved in ["CONTAINS"]:
                            newRelationType = "CONTAINS"
                    elif relation1Resolved == "ENDS-ON":
                        if relation2Resolved in ["BEFORE", "CONTAINS", "ENDS-ON"]:
                            newRelationType = "BEFORE"
                    elif relation1Resolved == "BEGINS-ON":
                        if relation2Resolved in ["AFTER", "CONTAINS", "BEGINS-ON"]:
                            newRelationType = "AFTER"

                    if newRelationType == "":
                        continue

                    # Reverse the relation again if necessary, since ThymeML does not use AFTER or DURING relations
                    shouldReverseNewRelation = False
                    if newRelationType == "AFTER":
                        newRelationType = "BEFORE"
                        shouldReverseNewRelation = True
                    elif newRelationType == "DURING":
                        newRelationType = "CONTAINS"
                        shouldReverseNewRelation = True

                    source = relation1.properties["Target"] if relation1Reversed else relation1.properties["Source"] 
                    target = relation2.properties["Source"] if relation2Reversed else relation2.properties["Target"]

                    if shouldReverseNewRelation:
                        tempReference = source
                        source = target
                        target = tempReference

                    # Create new temporal relation
                    newRelationID = str(len(relations) + 1) + "@" + documentName + "@gold"

                    newRelationXMLString = """<relation>
                                        <id>""" + newRelationID + """</id>
                                        <type>TLINK</type>
                                        <parentsType>TemporalRelations</parentsType>
                                        <properties>
                                        <Source>""" + source.id + """</Source>
                                        <Type>""" + newRelationType + """</Type>
                                        <Target>""" + target.id + """</Target>
                                        </properties>
                                        </relation>"""
                    newRelationXML = ElementTree.fromstring(newRelationXMLString)
                    newRelation = ThymeMLRelation(newRelationXML, data.annotations, documentContents)

                    relationAlreadyExists = False
                    for relation in tlinkRelations:
                        if relation.properties["Source"].id == source.id and relation.properties["Target"].id == target.id and relation.properties["Type"] == newRelationType:
                            relationAlreadyExists = True
                            break
                        
                    if not relationAlreadyExists:
                        # print "\tApplying temporal closure"

                        # print "\t\tR1: " + relation1.properties["Source"].id + " " + relation1.properties["Type"] + " " + relation1.properties["Target"].id
                        # print "\t\t    " + str(relation1.properties["Source"].spansContent) + " " + relation1.properties["Type"] + " " + str(relation1.properties["Target"].spansContent)
                        # if "OriginalSource" in relation1.properties or "OriginalTarget" in relation1.properties:
                        #     originalSource = relation1.properties["OriginalSource"] if "OriginalSource" in relation1.properties else relation1.properties["Source"]
                        #     originalTarget = relation1.properties["OriginalTarget"] if "OriginalTarget" in relation1.properties else relation1.properties["Target"]
                        #     print "\t\t    " + originalSource.id + " " + len(relation.properties["Type"])*" " + " " + originalTarget.id
                        #     print "\t\t    " + str(originalSource.spansContent) + " " + relation1.properties["Type"] + " " + str(originalTarget.spansContent)

                        # print "\t\tR2: " + relation2.properties["Source"].id + " " + relation2.properties["Type"] + " " + relation2.properties["Target"].id
                        # print "\t\t    " + str(relation2.properties["Source"].spansContent) + " " + relation2.properties["Type"] + " " + str(relation2.properties["Target"].spansContent)
                        # if "OriginalSource" in relation2.properties or "OriginalTarget" in relation2.properties:
                        #     originalSource = relation2.properties["OriginalSource"] if "OriginalSource" in relation2.properties else relation2.properties["Source"]
                        #     originalTarget = relation2.properties["OriginalTarget"] if "OriginalTarget" in relation2.properties else relation2.properties["Target"]
                        #     print "\t\t    " + originalSource.id + " " + len(relation.properties["Type"])*" " + " " + originalTarget.id
                        #     print "\t\t    " + str(originalSource.spansContent) + " " + relation2.properties["Type"] + " " + str(originalTarget.spansContent)

                        # print "\t\tR3: " + newRelation.properties["Source"].id + " " + newRelation.properties["Type"] + " " + newRelation.properties["Target"].id
                        # print "\t\t    " + str(newRelation.properties["Source"].spansContent) + " " + newRelation.properties["Type"] + " " + str(newRelation.properties["Target"].spansContent)
                        # if "OriginalSource" in newRelation.properties or "OriginalTarget" in newRelation.properties:
                        #     originalSource = newRelation.properties["OriginalSource"] if "OriginalSource" in newRelation.properties else newRelation.properties["Source"]
                        #     originalTarget = newRelation.properties["OriginalTarget"] if "OriginalTarget" in newRelation.properties else newRelation.properties["Target"]
                        #     print "\t\t    " + originalSource.id + " " + len(relation.properties["Type"])*" " + " " + originalTarget.id
                        #     print "\t\t    " + str(originalSource.spansContent) + " " + relanewRelationtion2.properties["Type"] + " " + str(originalTarget.spansContent)

                        foundImplicitRelation = True
                        tlinkRelations.append(newRelation)
                        implicitRelationCount += 1

                # else: # There should be exactly 4 unique annotations (0 overlapping references)
                    # print ""
                    # print "\t\tRelations have nothing in common"

                    # if len(uniqueReferences) is not 4:
                        # print "\tERROR: There should always be 4 unique annotations when there is no relationship between the 2 relations. Found (" + str(len(uniqueReferences)) + ")"

    print "\tCreated " + str(implicitRelationCount) + " new relations"
    
    printSectionDivider(1)
    print "Found (" + str(len(conflictingRelationPairs)) + ") conflicting relation(s)..."

    for (relation1, relation2) in conflictingRelationPairs:

        identityCoreferenceConflict = type(relation1.properties["Source"]) is ThymeMLRelation or type(relation2.properties["Source"]) is ThymeMLRelation 
        if identityCoreferenceConflict:
            print "\tConflict (due to identity coreference chain):"
        else:
            print "\tConflict (due to temporal closure):"
        print "\t\tR1: " + relation1.properties["Source"].id + " " + relation1.properties["Type"] + " " + relation1.properties["Target"].id
        print "\t\t\t" + str(relation1.spansContent) + " " + relation1.properties["Type"] + " " + str(relation1.spansContent)
        if ("OriginalSource" in relation1.properties or "OriginalTarget" in relation1.properties) and not identityCoreferenceConflict:
            originalSource = relation1.properties["OriginalSource"] if "OriginalSource" in relation1.properties else relation1.properties["Source"]
            originalTarget = relation1.properties["OriginalTarget"] if "OriginalTarget" in relation1.properties else relation1.properties["Target"]
            print "\t\t    " + originalSource.id + " " + len(relation.properties["Type"])*" " + " " + originalTarget.id
            print "\t\t\t" + str(originalSource.spansContent) + " " + relation1.properties["Type"] + " " + str(originalTarget.spansContent)

        print "\t\tR2: " + relation2.properties["Source"].id + " " + relation2.properties["Type"] + " " + relation2.properties["Target"].id
        print "\t\t\t" + str(relation2.spansContent) + " " + relation2.properties["Type"] + " " + str(relation2.spansContent)
        if ("OriginalSource" in relation2.properties or "OriginalTarget" in relation2.properties) and not identityCoreferenceConflict:
            originalSource = relation2.properties["OriginalSource"] if "OriginalSource" in relation2.properties else relation2.properties["Source"]
            originalTarget = relation2.properties["OriginalTarget"] if "OriginalTarget" in relation2.properties else relation2.properties["Target"]
            print "\t\t    " + originalSource.id + " " + len(relation.properties["Type"])*" " + " " + originalTarget.id
            print "\t\t\t" + str(originalSource.spansContent) + " " + relation2.properties["Type"] + " " + str(originalTarget.spansContent)

    printSectionDivider(1)
    selfReferentialRelations = []
    print "Searching for self-referential temporal relations"
    for relation in tlinkRelations:
        if relation.properties["Source"] is relation.properties["Target"]:
            selfReferentialRelations.append(relation)
            print "\t\t R: " + relation.properties["Source"].id + " " + relation.properties["Type"] + " " + relation.properties["Target"].id
            print "\t\t\t" + str(relation.spansContent) + " " + relation.properties["Type"] + " " + str(relation.spansContent)
            if "OriginalSource" in relation.properties or "OriginalTarget" in relation.properties:
                originalSource = relation.properties["OriginalSource"] if "OriginalSource" in relation.properties else relation.properties["Source"]
                originalTarget = relation.properties["OriginalTarget"] if "OriginalTarget" in relation.properties else relation.properties["Target"]
                print "\t\t    " + originalSource.id + " " + len(relation.properties["Type"])*" " + " " + originalTarget.id
                print "\t\t\t" + str(originalSource.spansContent) + " " + relation.properties["Type"] + " " + str(originalTarget.spansContent)
    if len(selfReferentialRelations) == 0:
        print "\tNone Found" 

def mergeCoreferentEventsInTemporalRelations(temporalRelations, coreferenceChains):

    replaced = 0
    total = 0

    for temporalRelation in temporalRelations:

        for coreferenceChain in coreferenceChains:

            references = coreferenceChain.allReferences

            # Source
            if temporalRelation.properties["Source"] in references:
                # print "Found TLINK relation with Source belonging to a coreference chain relation"
                temporalRelation.properties["OriginalSource"] = temporalRelation.properties["Source"] 
                temporalRelation.properties["Source"] = coreferenceChain
                replaced += 1

            # Target
            if temporalRelation.properties["Target"] in references:
                # print "Found TLINK relation with Target belonging to a coreference chain relation"
                temporalRelation.properties["OriginalTarget"] = temporalRelation.properties["Target"]
                temporalRelation.properties["Target"] = coreferenceChain
                replaced += 1

    print "\tTemporal Relation Components Replaced with Coreference Chains " + str(replaced) + "/" + str(len(temporalRelations)*2)