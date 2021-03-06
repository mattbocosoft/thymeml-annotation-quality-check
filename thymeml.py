import collections
import functools
import os
import re
import sys

try:
    import xml.etree.cElementTree as ElementTree
except ImportError:
    import xml.etree.ElementTree as ElementTree


def walk(root, xml_name_regex="[.]xml$"):
    """
    :param root: directory containing ThymeML XML directories
    :param str xml_name_regex: regular expression identifying .xml files to include
    :return iterator: an iterator of (sub-dir, text-file-name, xml-file-names) where sub-dir is the path to the ThymeML
        directory relative to root, text-file-name is the name of the ThymeML text file, and xml-file-names is a list
        of names of ThymeML XML files
    """
    for dir_path, dir_names, file_names in os.walk(root):
        if not dir_names:
            sub_dir = ''
            if dir_path.startswith(root):
                sub_dir = dir_path[len(root):]
                if sub_dir.startswith(os.path.sep):
                    sub_dir = sub_dir[len(os.path.sep):]
            xml_names = [file_name for file_name in file_names if re.search(xml_name_regex, file_name) is not None]
            if xml_names:
                text_name = os.path.basename(dir_path)
                yield sub_dir, text_name, xml_names


def walk_ThymeML_to_ThymeML(root, xml_name_regex="[.]xml$"):
    """
    :param str root: path of the root directory to be walked
    :param str xml_name_regex: regular expression identifying .xml files to include
    :return iterator: an iterator of (input-sub-dir, output-sub-dir, text-file-name, xml-file-names)
    """
    for sub_dir, text_name, xml_names in walk(root, xml_name_regex):
        yield sub_dir, sub_dir, text_name, xml_names


def walk_flat_to_ThymeML(text_dir):
    """
    :param str text_dir: path to a directory of text files (and no subdirectories)
    :return iterator: an iterator of (input-sub-dir, output-sub-dir, text-file-name, xml-file-names)
    """
    for file_name in os.listdir(text_dir):
        yield '', file_name, file_name, []


class _XMLWrapper(object):
    def __init__(self, xml):
        """
        :param xml.etree.ElementTree.Element xml: the XML element to be wrapped in an object
        """
        self.xml = xml

    def __repr__(self):
        if self.xml is not None:
            result = ElementTree.tostring(self.xml)
            if sys.version_info.major >= 3:
                result = result.decode('utf-8')
        else:
            result = '{0}()'.format(self.__class__.__name__)
        return result


class ThymeMLData(_XMLWrapper):
    def __init__(self, xml=None, document=None):
        """
        :param xml.etree.ElementTree.Element xml: the <data> element
        """
        if xml is None:
            xml = ElementTree.Element("data")
        _XMLWrapper.__init__(self, xml)
        self.annotations = ThymeMLAnnotations(self.xml.find("annotations"), self, document)

    @classmethod
    def from_file(cls, xml_path, document):
        try:
            return cls(ElementTree.parse(xml_path).getroot(), document)
        except ElementTree.ParseError as e:
            raise ValueError("invalid XML file {0}: {1}".format(xml_path, e))

    def indent(self, string="\t"):
        # http://effbot.org/zone/element-lib.htm#prettyprint
        def _indent(elem, level=0):
            i = "\n" + level * string
            if len(elem):
                if not elem.text or not elem.text.strip():
                    elem.text = i + string
                if not elem.tail or not elem.tail.strip():
                    elem.tail = i
                for elem in elem:
                    _indent(elem, level + 1)
                if not elem.tail or not elem.tail.strip():
                    elem.tail = i
            else:
                if level and (not elem.tail or not elem.tail.strip()):
                    elem.tail = i
        _indent(self.xml)

    def to_file(self, xml_path):
        ElementTree.ElementTree(self.xml).write(xml_path, encoding="UTF-8", xml_declaration=True)


class ThymeMLAnnotations(_XMLWrapper):
    def __init__(self, xml, _data, document):
        _XMLWrapper.__init__(self, xml)
        self._data = _data
        self._id_to_annotation = collections.OrderedDict()
        if self.xml is not None:
            for annotation_elem in self.xml:
                if annotation_elem.tag == "entity":
                    annotation = ThymeMLEntity(annotation_elem, self, document)
                elif annotation_elem.tag == "relation":
                    annotation = ThymeMLRelation(annotation_elem, self, document)
                else:
                    raise ValueError("invalid tag: {0}".format(annotation_elem.tag))
                while annotation.id in self._id_to_annotation:
                    # raise ValueError("duplicate id: {0}".format(annotation.id))
                    print "\t\tDuplicate annotation id (" + annotation.id + "). Appending disambiguation suffix..."
                    annotation.id += "(d)"
                self._id_to_annotation[annotation.id] = annotation

    def __iter__(self):
        return iter(self._id_to_annotation.values())

    def append(self, annotation):
        """
        :param ThymeMLAnnotation annotation: the annotation to add
        """
        if annotation.id is None:
            raise ValueError("no id defined for {0}".format(annotation))
        if annotation.id in self._id_to_annotation:
            raise ValueError("duplicate id: {0}".format(annotation.id))
        annotation._annotations = self
        if self.xml is None:
            self.xml = ElementTree.SubElement(self._data.xml, "annotations")
        self.xml.append(annotation.xml)
        self._id_to_annotation[annotation.id] = annotation

    def remove(self, annotation):
        """
        :param ThymeMLAnnotation annotation: the annotation to remove
        """
        if annotation.id is None:
            raise ValueError("no id defined for {0}".format(annotation))
        self.xml.remove(annotation.xml)
        del self._id_to_annotation[annotation.id]

    def select_id(self, id):
        return self._id_to_annotation[id]

    def select_type(self, type_name):
        for annotation in self:
            if annotation.type == type_name:
                yield annotation

    def find_self_referential(self):
        for annotation in self:
            if annotation.is_self_referential():
                return annotation


@functools.total_ordering
class ThymeMLAnnotation(_XMLWrapper):
    def __init__(self, xml, _annotations, document):
        """
        :param xml.etree.ElementTree.Element xml: xml definition of this annotation
        :param ThymeMLAnnotations _annotations: the annotations collection containing this annotation
        """
        _XMLWrapper.__init__(self, xml)
        self._annotations = _annotations
        self.document = document
        self.properties = ThymeMLProperties(self.xml.find("properties"), self)

    def __eq__(self, other):
        return (
            isinstance(other, ThymeMLAnnotation) and
            self.spans == other.spans and
            self.type == other.type and
            self.parents_type == other.parents_type and
            self.properties == other.properties)

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        result = hash(self.spans)
        result = 31 * result + hash(self.type)
        result = 31 * result + hash(self.parents_type)
        # result = 31 * result + hash(self.properties)
        return result

    def __lt__(self, other):
        return self.spans < other.spans

    @property
    def id(self):
        return self.xml.findtext("id")

    @id.setter
    def id(self, value):
        id_elem = self.xml.find("id")
        if id_elem is None:
            id_elem = ElementTree.SubElement(self.xml, "id")
        id_elem.text = value

    @property
    def type(self):
        return self.xml.findtext("type")

    @type.setter
    def type(self, value):
        type_elem = self.xml.find("type")
        if type_elem is None:
            type_elem = ElementTree.SubElement(self.xml, "type")
        type_elem.text = value

    @property
    def parents_type(self):
        return self.xml.findtext("parentsType")

    @parents_type.setter
    def parents_type(self, value):
        parents_type_elem = self.xml.find("parentsType")
        if parents_type_elem is None:
            parents_type_elem = ElementTree.SubElement(self.xml, "parentsType")
        parents_type_elem.text = value

    @property
    def spans(self):
        raise NotImplementedError

    @property
    def flatSpans(self):
        raise NotImplementedError

    @property
    def spansContent(self):
        raise NotImplementedError

    def is_self_referential(self, seen_ids=None):
        if seen_ids is None:
            seen_ids = {}
        seen_ids[id(self)] = self
        for name in self.properties:
            value = self.properties[name]
            if seen_ids is not None and id(value) in seen_ids:
                return True
            if isinstance(value, ThymeMLAnnotation):
                if value.is_self_referential(dict(seen_ids)):
                    return True
        return False

class ThymeMLProperties(_XMLWrapper):
    def __init__(self, xml, _annotation):
        """
        :param xml.etree.ElementTree.Element xml: a <properties> element
        :param ThymeMLAnnotation _annotation: the annotation containing these properties
        """
        _XMLWrapper.__init__(self, xml)
        self._annotation = _annotation
        self._tag_to_property_xml = {}
        if self.xml is not None:
            for property_elem in self.xml:

                keyExists = property_elem.tag in self._tag_to_property_xml

                useList = False                
                if (property_elem.tag == "Coreferring_String" or # We know these keys should map to a list
                    property_elem.tag == "Part" or
                    property_elem.tag == "Subset"):
                    useList = True
                elif keyExists: # Key/Value already exists
                    print "PROPERTY (" + property_elem.tag + ") ALREADY EXISTS"
                    useList = True

                if useList:
                    if keyExists:
                        self._tag_to_property_xml[property_elem.tag].append(property_elem)
                    else:
                        self._tag_to_property_xml[property_elem.tag] = [property_elem]
                else: # Set value # Key/Value does not exist
                    self._tag_to_property_xml[property_elem.tag] = property_elem

    def __eq__(self, other):
        if not isinstance(other, ThymeMLProperties):
            return False
        for name in self:
            self_value = self[name]
            if name not in other._tag_to_property_xml:
                return False
            other_value = other[name]
            if self_value != other_value:
                return False
        for name in other:
            if name not in self._tag_to_property_xml:
                return False
        return True

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        result = 0
        for name in self:
            result += hash(name)
            result += hash(self[name])
        return result

    def __iter__(self):
        return iter(self._tag_to_property_xml)

    def __contains__(self, property_name):
        return property_name in self._tag_to_property_xml

    def __getitem__(self, property_name):
        value = self._tag_to_property_xml[property_name]
        if type(value) is list:
            valueList = []
            for item in value:
                valueList.append(self._annotation._annotations._id_to_annotation.get(item.text, item.text))
            return valueList
        else:
            valueText = self._tag_to_property_xml[property_name].text
            return self._annotation._annotations._id_to_annotation.get(valueText, valueText)

    def __setitem__(self, name, value):        
        if isinstance(value, ThymeMLAnnotation):
            if self._annotation is None or self._annotation._annotations is None:
                message = 'annotation must be in <annotations> before assigning annotation value to property "{0}":\n{1}'
                raise ValueError(message.format(name, self._annotation))
            if value != self._annotation._annotations._id_to_annotation.get(value.id):
                message = 'annotation must be in <annotations> before assigning it to property "{0}":\n{1}'
                raise ValueError(message.format(name, value))
        if self.xml is None:
            self.xml = ElementTree.SubElement(self._annotation.xml, "properties")
        property_elem = self.xml.find(name)
        if property_elem is None:
            property_elem = ElementTree.SubElement(self.xml, name)
            self._tag_to_property_xml[name] = property_elem
        if isinstance(value, ThymeMLAnnotation):
            property_elem.text = value.id
        else:
            property_elem.text = value

    def __delitem__(self, name):
        if name not in self._tag_to_property_xml:
            raise ValueError('no such property {0!r}'.format(name))
        self.xml.remove(self._tag_to_property_xml.pop(name))
        if not self._tag_to_property_xml:
            self._annotation.xml.remove(self.xml)
            self.xml = None

    def items(self):
        return [(name, self[name]) for name in self]


class ThymeMLEntity(ThymeMLAnnotation):
    def __init__(self, xml=None, _annotations=None, document=None):
        if xml is None:
            xml = ElementTree.Element("entity")
        ThymeMLAnnotation.__init__(self, xml, _annotations, document)

    @property
    def spans(self):
        spans_text = self.xml.findtext("span")
        if spans_text is None:
            return ()
        return tuple(tuple(int(offset) for offset in tuple(span_text.split(",")))
                     for span_text in spans_text.split(";"))

    @property
    def flatSpans(self):
        return self.spans

    @property
    def spansContent(self):
        contentSpans = []
        for span in self.spans:
            if len(span) == 2:
                contentSpans.append(self.document[span[0]:span[1]])
        return contentSpans

    @spans.setter
    def spans(self, spans):
        if not isinstance(spans, tuple) or not all(isinstance(span, tuple) and len(span) == 2 for span in spans):
            raise ValueError("spans must be a tuple of pairs")
        span_elem = self.xml.find("span")
        if span_elem is None:
            span_elem = ElementTree.SubElement(self.xml, "span")
        span_elem.text = ";".join("{0:d},{1:d}".format(*span) for span in spans)

class ThymeMLRelation(ThymeMLAnnotation):
    def __init__(self, xml=None, _annotations=None, document=None):
        if xml is None:
            xml = ElementTree.Element("relation")
        ThymeMLAnnotation.__init__(self, xml, _annotations, document)

    @property
    def spans(self):
        return tuple(
            self.properties[name].spans
            for name in sorted(self.properties)
            if isinstance(self.properties[name], ThymeMLAnnotation))
    
    @property
    def flatSpans(self):
        subSpanList = list(
            reference.flatSpans
            for reference in self.allReferences)
        flatten = []
        for item in subSpanList:
            if type(item) is tuple:
                flatten += item
            else:
                flatten.extend(item)
        return flatten

    @property
    def spansContent(self):
        contentSpans = []
        for span in self.flatSpans:
            contentSpans.append(self.document[span[0]:span[1]])
        return contentSpans
    
    @property
    def allReferences(self):
        references = []  
        if self.parents_type == "CorefChains":
            if self.type == "Identical":
                references = [self.properties["FirstInstance"]]
                if type(self.properties["Coreferring_String"]) is not list:
                    print "ERROR: Coreferring_String is not LIST. Type is " + str(type())
                references.extend(self.properties["Coreferring_String"])
            elif self.type == "Whole/Part":
                references = [self.properties["Whole"]]
                if type(self.properties["Part"]) is not list:
                    print "ERROR: Part is not LIST. Type is " + str(type())
                references.extend(self.properties["Part"])
        elif self.parents_type == "TemporalRelations":
            if self.type == "TLINK" or self.type == "ALINK":
                references = [self.properties["Source"], self.properties["Target"]]
            else:
                print "Could not find references for temporal relation subtype: " + self.type
        return references
