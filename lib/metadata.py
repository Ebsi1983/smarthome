#!/usr/bin/env python3
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
# Copyright 2017-       Martin Sinn                         m.sinn@gmx.de
#########################################################################
#  This file is part of SmartHomeNG
#
#  SmartHomeNG is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  SmartHomeNG is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with SmartHomeNG  If not, see <http://www.gnu.org/licenses/>.
#########################################################################

import logging
import os

from lib.utils import Utils
import lib.shyaml as shyaml
from lib.constants import (YAML_FILE, FOO, META_DATA_TYPES, META_DATA_DEFAULTS)

META_PARAMETER_SECTION = 'parameters'
#META_DATA_TYPES=['bool', 'int', 'float', 'str', 'list', 'dict', 'ip', 'mac', 'foo']
#META_DATA_DEFAULTS={'bool': False, 'int': 0, 'float': 0.0, 'str': '', 'list': [], 'dict': {}, 'OrderedDict': {}, 'num': 0, 'scene': 0, 'ip': '0.0.0.0', 'mac': '00:00:00:00:00:00', 'foo': None}


logger = logging.getLogger(__name__)

class Metadata():

    default_language = 'de'   # in the future: to be read from the smarthome object
    
    def __init__(self, sh, addon_name, addon_type, classpath=''):
        self._sh = sh
        self._addon_name = addon_name.lower()
        self._addon_type = addon_type
        self._paramlist = []

        self._log_premsg = "Metadata {} '{}': ".format(addon_type, self._addon_name)

#        logger.warning(self._log_premsg+"classpath = '{}'".format( classpath ) )
        if classpath == '':
            if addon_type == 'plugin':
                addon_type_dir = 'plugins'
            elif addon_type == 'module':
                addon_type_dir = 'modules'
            else:
                return
            self.relative_filename = os.path.join( addon_type_dir, self._addon_name, addon_type+YAML_FILE )
        else:
            self.relative_filename = os.path.join( classpath.replace('.', os.sep), addon_type+YAML_FILE )
#        logger.warning(self._log_premsg+"relative_filename = '{}'".format( self.relative_filename ) )
        
        basedir = self._sh.getBaseDir()
        filename = os.path.join( self._sh.getBaseDir(), self.relative_filename )
        self.meta = shyaml.yaml_load(filename, ordered=True)
        if self.meta != None:
            self.parameters = self.meta.get(META_PARAMETER_SECTION)
            if self.parameters != None:
                self._paramlist = list(self.parameters.keys())
        logger.info(self._log_premsg+"Metadata paramlist = '{}'".format( str(self._paramlist) ) )

        # Test parameter definitions for validity
        for param in self._paramlist:
            logger.info(self._log_premsg+"param = '{}'".format( str(param) ) )
            if self.parameters[param] != None:
                typ = str(self.parameters[param].get('type', FOO)).lower()
                # to be implemented: timeframe
                if not (typ in META_DATA_TYPES):
                    logger.error(self._log_premsg+"Invalid definition in metadata file '{}': type '{}' for parameter '{}' -> using type '{}' instead".format( self.relative_filename, typ, param, FOO ) )
                    self.parameters[param]['type'] = FOO
            else:
#                self.parameters[param]['type'] = FOO
                pass
            
        # Read global metadata for addon
        
        if self.meta != None:
            self.addon_metadata = self.meta.get(addon_type)
        else:
            self.addon_metadata = None
        
    
    def _strip_quotes(self, string):
        if type(string) is str:
            string = string.strip()
            if len(string) >= 2:
                if string[0] in ['"', "'"]:  # check if string starts with ' or "
                    if string[0] == string[-1]:  # and end with it
                        if string.count(string[0]) == 2:  # if they are the only one
                            string = string[1:-1]  # remove them
        return string


    # ------------------------------------------------------------------------
    # Methods for global values
    #

    def get_string(self, key):
        """
        Return the value for a global key as a string
        
        :param key: global key to look up (in section 'plugin' or 'module')
        :type key: str
        
        :return: value for the key
        :rtype: str
        """
        if self.addon_metadata == None:
            return ''

        return self.addon_metadata.get(key, '')
        

    def get_mlstring(self, mlkey):
        """
        Return the value for a global multilanguage-key as a string
        
        It trys to lookup th value for the default language. 
        If the value for the default language is empty, it trys to look up the value for English.
        If there is no value for the default language and for English, it trys to lookup the value for German.
        
        :param key: global multilabguage-key to look up (in section 'plugin' or 'module')
        :type key: str
        
        :return: value for the key
        :rtype: str
        """
        if self.addon_metadata == None:
            return ''

        key_dict = self.addon_metadata.get(mlkey)
        if key_dict == None:
            return ''
        result = self.addon_metadata.get(mlkey, '')
        if result == '':
            result = key_dict.get(self.default_language, '')
            if result == '':
                result = key_dict.get('en','')
                if result == '':
                    result = key_dict.get('de','')
        return result
        
    
    # ------------------------------------------------------------------------
    # Methods for parameter checking
    #

    def _get_type(self, param):
        """
        Returns the type of a parameter
        """
        if self.parameters[param] == None:
            return FOO
        return str(self.parameters[param].get('type', FOO)).lower()
        
        
    def _test_valuetype(self, typ, value):
        """
        Returns True, if the value can be converted to the specified type
        """
        if typ == 'bool':
            return (Utils.to_bool(value, default='?') != '?')
        elif typ == 'int':
            return Utils.is_int(value)
        elif typ in ['float','num']:
            return Utils.is_float(value)
        elif typ == 'scene':
            if Utils.is_int(value):
                return (int(value) >= 0) and (int(value) < 256)
            else:
                return False
        elif typ == 'str':
#            return (type(value) is str)
            return True     # Everything can be converted to a string
        elif typ == 'list':
            return (type(value) is list)
        elif typ == 'dict':
            return (type(value) is dict)
        elif typ == 'ip':
            return Utils.is_ip(value)
        elif typ == 'mac':
            return Utils.is_mac(value)
        elif typ == FOO:
            return True

    
    def _test_value(self, param, value):
        """
        Returns True, if the value can be converted to specified type
        """
        if param in self._paramlist:
            typ = self._get_type(param)
            return self._test_valuetype(typ, value)
        return False
    

    def _convert_valuetotype(self, typ, value):
        """
        Returns the value converted to the parameters type
        """
        if typ == 'bool':
            result = Utils.to_bool(value)
        elif typ in ['int','scene']:
            result = int(value)
        elif typ in ['float','num']:
            result = float(value)
        elif typ == 'str':
            result = str(value)
        elif typ == 'list':
            result = list(value)
        elif typ == 'dict':
            result = dict(value)
        elif typ in ['ip', 'mac']:
            result = str(value)
        elif typ == FOO:
            result = value
        else:
            logger.error(self._log_premsg+"unhandled type {}".format(typ))
        return result
        
            
    def _convert_value(self, param, value, is_default=False):
        """
        Returns the value converted to the parameters type
        """
        result = False
        if param in self._paramlist:
            typ = self._get_type(param)
            result = self._convert_valuetotype(typ, value)

            orig = result
            result = self._test_validity(param, result, is_default)
            if result != orig:
                # Für non-default Prüfung nur Warning
                logger.error(self._log_premsg+"Invalid default '{}' in metadata file '{}' for parameter '{}' -> using '{}' instead".format( orig, self.relative_filename, param, result ) )
        return result
    

    def _test_validity(self, param, value, is_default=False):
        """
        Checks the value against a list of valid values.
        If valid, it returns the value. 
        Otherwise it returns the first entry of the list of valid values.
        """
        result = value
        if self.parameters[param] != None:
            if self.parameters[param].get('type') in ['int', 'float', 'num', 'scene']:
                valid_min = self.parameters[param].get('valid_min')
                if valid_min != None:
                    if self._test_value(param, valid_min):
                        if result < self._convert_valuetotype(self._get_type(param), valid_min):
                            if is_default == False:
                                result = self._get_defaultvalue(param)   # instead of valid_min
                            else:
                                result = valid_min
                valid_max = self.parameters[param].get('valid_max')
                if valid_max != None:
                    if self._test_value(param, valid_max):
                        if result > self._convert_valuetotype(self._get_type(param), valid_max):
                            if is_default == False:
                                result = self._get_defaultvalue(param)   # instead of valid_max
                            else:
                                result = valid_max
        
        if self.parameters[param] == None:
            logger.warning(self._log_premsg+"_test_validity: param {}".format(param))
        else:
            valid_list = self.parameters[param].get('valid_list')
            if (valid_list == None) or (len(valid_list) == 0):
                pass
            else:
                if result in valid_list:
                    pass
                else:
                    result = valid_list[0]
        return result

    def _get_default_if_none(self, typ):
        """
        Returns the default value for  datatype.
        It is used, if no default value is defined for a parameter.
        """
        return META_DATA_DEFAULTS.get(typ, None)
        
    
    def _get_defaultvalue(self, param):
        value = None
        if param in self._paramlist:
            if self.parameters[param] != None:
                if self._get_type(param) == 'dict':
                    if self.parameters[param].get('default') != None:
                        value = dict(self.parameters[param].get('default'))
                else:
                    value = self.parameters[param].get('default')
                typ = self._get_type(param)
                if value == None:
                    value = self._get_default_if_none(typ)
                    
                if not self._test_value(param, value):
                    # Für non-default Prüfung nur Warning
                    logger.error(self._log_premsg+"Invalid data for type '{}' in metadata file '{}': default '{}' for parameter '{}' -> using '{}' instead".format( self.parameters[param].get('type'), self.relative_filename, value, param, self._get_default_if_none(typ) ) )
                    value = None
                if value == None:
                    value = self._get_default_if_none(typ)

                self._convert_value(param, value, is_default=True)

                orig_value = value
                value = self._test_validity(param, value, is_default=True)
                if value != orig_value:
                    # Für non-default Prüfung nur Warning
                    logger.error(self._log_premsg+"Invalid default '{}' in metadata file '{}' for parameter '{}' -> using '{}' instead".format( orig_value, self.relative_filename, param, value ) )

        return value


    def check_parameters(self, args):
        """
        Checks the values of a dict of configured parameters. 
        
        Returns a dict with all defined parameters with values. It returns default values
        for parameters that have not been configured. The resulting dict contains the
        values in the the datatype of the parameter definition  

        :param args: Configuraed parameters with the values
        :type args: dict of parameter-values (values as string)
        
        :return: All defined parameters with values
        :rtype: dict of parameters with values (values in the the datatype of the parameter definition)
        """
        addon_params = {}
        if self.meta == None:
            logger.info(self._log_premsg+"No metadata found" )
            return addon_params
        if self.parameters == None:
            logger.info(self._log_premsg+"No parameter definitions found in metadata" )
            return addon_params
            
        for param in self._paramlist:
            value = Utils.strip_quotes(args.get(param))
            if value == None:
                addon_params[param] = self._get_defaultvalue(param)
                logger.debug(self._log_premsg+"'{}' not found in /etc/{}, using default value '{}'".format(param, self._addon_type+YAML_FILE, addon_params[param]))
            else:
                if self._test_value(param, value):
                    addon_params[param] = self._convert_value(param, value)
                    logger.debug(self._log_premsg+"Found '{}' with value '{}' in /etc/{}".format(param, value, self._addon_type+YAML_FILE))
                else:
                    addon_params[param] = self._get_defaultvalue(param)
                    logger.error(self._log_premsg+"Found invalid value '{}' for parameter '{}' in /etc/{}, using default value '{}' instead".format(value, param, self._addon_type+YAML_FILE, str(addon_params[param])))

        return addon_params
        
    