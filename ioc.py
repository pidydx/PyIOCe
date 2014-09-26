# Copyright 2014 Yahoo! Inc.  
# Licensed under the Apache 2.0 license.  Developed for Yahoo! by Sean Gillespie. 
#
# Yahoo! licenses this file to you under the Apache License, Version
# 2.0 (the "License"); you may not use this file except in compliance with the
# License.  You may obtain a copy of the License at:
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.  See the License for the specific language governing
# permissions and limitations under the License.

import os
from lxml import etree as et
import copy
import ioc_et
import wx

def strip_namespace(ioc_xml):
    if ioc_xml.tag.startswith('{'):
        ns_length = ioc_xml.tag.find('}')
        namespace = ioc_xml.tag[0:ns_length+1]
    for element in ioc_xml.getiterator():
        if element.tag.startswith(namespace):
            element.tag = element.tag[len(namespace):]  
    return ioc_xml

def generate_label(element):
    if element.tag == "Indicator":
        return (element.get('operator'), wx.BLACK)

    if element.tag == "IndicatorItem":
        color = wx.BLUE

        context = element.find('Context')
        content = element.find('Content')

        condition = ""
        search_type = ""
        search_path = ""
        search_text = ""

        if element.get('condition'):
            condition = element.get('condition')

        if context.get('type'):
            search_type = context.get('type')

        if context.get('search'):
            search_path = context.get('search')

        if content.text:
            search_text = content.text

        if "preserve-case" in element.keys():
            if element.get('preserve-case') == "true":
                color = "#009900"

        negate = ""
        if "negate" in element.keys():
            if element.get('negate') == "true":
                negate = " NOT"
                if element.get('preserve-case') == "true":
                    color = "#7300FF"
                else:
                    color = wx.RED


        if condition == "isnot":
            condition = "is"
            negate = " NOT"
            color = wx.RED

        if condition == "containsnot":
            condition = "contains"
            negate = " NOT"
            color = wx.RED
        
        label = negate + " " + search_type + ":" + search_path + " " + condition + " " + search_text
        return (label, color)
    return "Bad Indicator"

class IOC():
    def __init__(self, ioc_xml):
        self.working_xml = copy.deepcopy(ioc_xml)
        self.orig_xml = copy.deepcopy(ioc_xml)

        self.attributes = self.working_xml.attrib
        metadata_root = "TEST"

        if self.working_xml.nsmap[None] == "http://schemas.mandiant.com/2010/ioc":
            self.version = "1.0"
            metadata_root = self.working_xml

            self.criteria = self.working_xml.find('definition')
            if self.criteria == None:
                self.working_xml.append(ioc_et.make_definition_node(ioc_et.make_Indicator_node("OR")))
                self.criteria = self.working_xml.find('definition')

            self.parameters = None

        elif self.working_xml.nsmap[None] == "http://openioc.org/schemas/OpenIOC_1.1":
            self.version = "1.1"
            metadata_root = self.working_xml.find('metadata')
            if metadata_root == None:
                self.working_xml.append(ioc_et.make_metadata_node(name = "*Missing*", author = "*Missing*", description = "*Missing*", links=ioc_et.make_links_node()))
                metadata_root = self.working_xml.find('metadata')
            
            self.criteria = self.working_xml.find('criteria')
            if self.criteria == None:
                self.working_xml.append(ioc_et.make_criteria_node(ioc_et.make_Indicator_node("OR")))
                self.criteria = self.working_xml.find('criteria')

            self.parameters = self.working_xml.find('parameters')
            if self.parameters == None:
                self.working_xml.append(ioc_et.make_parameters_node())
                self.parameters = self.working_xml.find('parameters')

        self.name = metadata_root.find('short_description')
        if self.name == None:
            metadata_root.append(ioc_et.make_short_description_node("*Missing*"))
            self.name = metadata_root.find('short_description')

        self.desc = metadata_root.find('description')
        if self.desc == None:
            metadata_root.append(ioc_et.make_description_node("*Missing*"))
            self.desc = metadata_root.find('description')

        self.author = metadata_root.find('authored_by')
        if self.author == None:
            metadata_root.append(ioc_et.make_authored_by_node("*Missing*"))
            self.author = metadata_root.find('authored_by')

        self.created = metadata_root.find('authored_date')
        if self.created == None:
            metadata_root.append(ioc_et.make_authored_date_node())
            self.created = metadata_root.find('authored_date')

        self.links = metadata_root.find('links')
        if self.links == None:
            metadata_root.append(ioc_et.make_links_node())
            self.links = metadata_root.find('links')


    def get_uuid(self):
        return self.attributes['id']

    def get_name(self):
        return self.name.text

    def set_name(self, name):
        self.name.text = name

    def get_modified(self):
        return self.attributes['last-modified']

    def set_modified(self):
        self.attributes['last-modified'] = ioc_et.get_current_date()

    def get_author(self):
        return self.author.text

    def set_author(self, author):
        self.author.text = author

    def get_created(self):
        return self.created.text

    def set_created(self):
        self.created.text = ioc_et.get_current_date()

    def get_metadata(field):
        pass

    def get_desc(self):
        if self.desc.text is not None:
            return self.desc.text
        else:
            return ""

    def set_desc(self, desc):
        self.desc.text = desc

    def get_links(self):
        pass

    def get_indicator(self):
        pass

class IOCList():
    def __init__(self):
        self.working_dir = None
        self.iocs = {}

    def save_iocs(self, full_path=None):
        if full_path:
            if et.tostring(self.iocs[full_path].working_xml) != et.tostring(self.iocs[full_path].orig_xml):
                self.iocs[full_path].set_modified()
                ioc_xml_string = et.tostring(self.iocs[full_path].working_xml, encoding="utf-8", xml_declaration=True, pretty_print = True)
                ioc_file = open(full_path, 'w')
                ioc_file.write(ioc_xml_string)
                ioc_file.close()
                self.iocs[full_path].orig_xml = copy.deepcopy(self.iocs[full_path].working_xml)
        else:
            for full_path in self.iocs:
                if et.tostring(self.iocs[full_path].working_xml) != et.tostring(self.iocs[full_path].orig_xml):
                    self.iocs[full_path].set_modified()
                    ioc_xml_string = et.tostring(self.iocs[full_path].working_xml, encoding="utf-8", xml_declaration=True, pretty_print = True)
                    ioc_file = open(full_path, 'w')
                    ioc_file.write(ioc_xml_string)
                    ioc_file.close()
                    self.iocs[full_path].orig_xml = copy.deepcopy(self.iocs[full_path].working_xml)

    def clone_ioc(self,current_ioc):
        new_ioc_xml = copy.deepcopy(current_ioc.working_xml)
        new_uuid = ioc_et.get_guid()
        ioc_file = new_uuid + ".ioc"
        full_path = os.path.join(self.working_dir, ioc_file)
        
        new_ioc_xml.attrib['id'] = new_uuid
        self.iocs[full_path] = IOC(new_ioc_xml)
        self.iocs[full_path].set_modified()
        self.iocs[full_path].set_created()
        self.iocs[full_path].orig_xml = et.Element('Clone')

        return full_path

    def add_ioc(self, author, version):
        new_ioc_xml = ioc_et.make_IOC_root(version=version)

        ioc_file = new_ioc_xml.attrib['id'] + ".ioc"
        full_path = os.path.join(self.working_dir, ioc_file)

        if version == "1.0":
            new_ioc_xml.append(ioc_et.make_short_description_node(name = "*New IOC*"))
            new_ioc_xml.append(ioc_et.make_description_node(text="PyIOCe Generated IOC"))
            new_ioc_xml.append(ioc_et.make_authored_by_node(author = author))
            new_ioc_xml.append(ioc_et.make_authored_date_node())
            new_ioc_xml.append(ioc_et.make_links_node())
            new_ioc_xml.append(ioc_et.make_definition_node(ioc_et.make_Indicator_node("OR")))
        elif version == "1.1":
            new_ioc_xml.append(ioc_et.make_metadata_node( name = "*New IOC*", author = "PyIOCe", description = "PyIOCe Generated IOC"))
            new_ioc_xml.append(ioc_et.make_criteria_node(ioc_et.make_Indicator_node("OR")))
            new_ioc_xml.append(ioc_et.make_parameters_node())

        self.iocs[full_path] = IOC(new_ioc_xml)
        self.iocs[full_path].orig_xml = et.Element('New')

        return full_path

    def open_ioc_path(self,dir):
        self.iocs = {}
        self.working_dir = dir
        for base, sub, files in os.walk(self.working_dir):
            for filename in files:
                if os.path.splitext(filename)[1][1:].lower() == "ioc":
                    full_path = os.path.join(base, filename)

                    ioc_file = open(full_path, 'r')

                    try: 
                        ioc_xml = et.fromstring(ioc_file.read())

                        clean_ioc_xml = strip_namespace(ioc_xml)

                        self.iocs[full_path] = IOC(clean_ioc_xml)
                    except:
                        pass #FIXME Logging/Alerts for failed files