#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
JavaScript Documentation Generator
Copyright (C) 2014 Ishraq Ibne Ashraf <ishraq@tinkerforge.com>

generator_javascript_doc.py: Generator for JavaScript documentation

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public
License along with this program; if not, write to the
Free Software Foundation, Inc., 59 Temple Place - Suite 330,
Boston, MA 02111-1307, USA.
"""

import sys
import os
import shutil
import subprocess
import glob
import re

sys.path.append(os.path.split(os.getcwd())[0])
import common
import javascript_common

class JavaScriptDocDevice(javascript_common.JavaScriptDevice):
    def get_javascript_examples(self):
        def title_from_filename(filename):
            if filename.endswith('.js'):
                filename = filename.replace('Example', '').replace('.js', '')
                return common.underscore_to_space(filename) + ' (Node.js)'
            elif filename.endswith('.html'):
                filename = filename.replace('Example', '').replace('.html', '')
                return common.underscore_to_space(filename) + ' (HTML)'
            else:
                raise ValueError('Invalid filename ' + filename)

        return common.make_rst_examples(title_from_filename, self, '^Example.*\.(?:js|html)$', 'JavaScript')

    def get_javascript_methods(self, typ):
        methods = ''
        func_start = '.. javascript:function:: '
        cls = self.get_javascript_class_name()
        for packet in self.get_packets('function'):
            if packet.get_doc()[0] != typ:
                continue
            name = packet.get_headless_camel_case_name()
            params = packet.get_javascript_parameter_list()
            pd = packet.get_javascript_parameter_desc('in')
            r = packet.get_javascript_return_desc()
            d = packet.get_javascript_formatted_doc()
            desc = '{0}{1}{2}'.format(pd, r, d)
            if len(params) > 0:
                params += ", "
            func = '{0}{1}.{2}({3}[returnCallback], [errorCallback])\n{4}'.format(func_start,
                                                 cls,
                                                 name,
                                                 params,
                                                 desc)

            methods += func + '\n'

        return methods

    def get_javascript_callbacks(self):
        cbs = ''
        func_start = '.. javascript:attribute:: '
        cls = self.get_javascript_class_name()
        for packet in self.get_packets('callback'):
            param_desc = packet.get_javascript_parameter_desc('out')
            desc = packet.get_javascript_formatted_doc()

            func = '{0}{1}.CALLBACK_{2}\n{3}\n{4}'.format(func_start,
                                                          cls,
                                                          packet.get_upper_case_name(),
                                                          param_desc,
                                                          desc)
            cbs += func + '\n'

        return cbs

    def get_javascript_api(self):
        create_str = {
        'en': """
.. javascript:function:: new {1}(uid, ipcon)

 :param uid: string
 :param ipcon: IPConnection

 Creates an object with the unique device ID ``uid``:

 .. code-block:: javascript

    var {3} = new {1}("YOUR_DEVICE_UID", ipcon);

 This object can then be used after the IP Connection is connected
 (see examples :ref:`above <{0}_{2}_javascript_examples>`).
""",
        'de': """
.. javascript:function:: new {1}(uid, ipcon)

 :param uid: string
 :param ipcon: IPConnection

 Erzeugt ein Objekt mit der eindeutigen Geräte ID ``uid``:

 .. code-block:: javascript

    var {3} = new {1}("YOUR_DEVICE_UID", ipcon)

 Dieses Objekt kann benutzt werden, nachdem die IP Connection verbunden ist
 (siehe Beispiele :ref:`oben <{0}_{2}_javascript_examples>`).
"""
        }

        register_str = {
        'en': """
.. javascript:function:: {1}.on(id, callback)

 :param id: int
 :param callback: function

 Registers a callback with ID *id* to the function *callback*. The available
 IDs with corresponding function signatures are listed
 :ref:`below <{0}_{2}_javascript_callbacks>`.
""",
        'de': """
.. javascript:function:: {1}.on(id, callback)

 :param id: int
 :param callback: function

 Registriert einen Callback mit der ID *id* mit der Funktion *callback*. Die
 verfügbaren IDs mit den zugehörigen Funktionssignaturen sind
 :ref:`unten <{0}_{2}_javascript_callbacks>` zu finden.
"""
        }

        c_str = {
        'en': """
.. _{1}_{2}_javascript_callbacks:

Callbacks
^^^^^^^^^

Callbacks can be registered to receive
time critical or recurring data from the device. The registration is done
with the :javascript:func:`on() <{3}.on>` function of
the device object. The first parameter is the callback ID and the second
parameter the callback function:

.. code-block:: javascript

    {4}.on({3}.CALLBACK_EXAMPLE,
        function (param) {{
            console.log(param);    
        }}
    );

The available constants with inherent number and type of parameters are
described below.

.. note::
 Using callbacks for recurring events is *always* preferred
 compared to using getters. It will use less USB bandwidth and the latency
 will be a lot better, since there is no round trip time.

{0}
""",
        'de': """
.. _{1}_{2}_javascript_callbacks:

Callbacks
^^^^^^^^^

Callbacks können registriert werden um zeitkritische
oder wiederkehrende Daten vom Gerät zu erhalten. Die Registrierung kann
mit der Funktion :javascript:func:`on() <{3}.on>` des
Geräte Objektes durchgeführt werden. Der erste Parameter ist die Callback ID
und der zweite Parameter die Callback-Funktion:

.. code-block:: javascript

    {4}.on({3}.CALLBACK_EXAMPLE,
        function (param) {{
            console.log(param);    
        }}
    );

Die verfügbaren Konstanten mit der dazugehörigen Parameteranzahl und -typen werden
weiter unten beschrieben.

.. note::
 Callbacks für wiederkehrende Ereignisse zu verwenden ist
 *immer* zu bevorzugen gegenüber der Verwendung von Abfragen.
 Es wird weniger USB-Bandbreite benutzt und die Latenz ist
 erheblich geringer, da es keine Paketumlaufzeit gibt.

{0}
"""
        }

        api = {
        'en': """
{0}
API
---

Generally, every method of the JavaScript binding takes two optional parameters,
``returnCallback`` and ``errorCallback``. These are two user defined callback functions.
``returnCallback`` is called when a return value is expected with the value as the
function's argument and ``errorCallback`` is called in case of an error with an error code.
The error code can be one of the following:

* IPConnection.ERROR_ALREADY_CONNECTED = 11
* IPConnection.ERROR_NOT_CONNECTED = 12
* IPConnection.ERROR_CONNECT_FAILED = 13
* IPConnection.ERROR_INVALID_FUNCTION_ID = 21
* IPConnection.ERROR_TIMEOUT = 31
* IPConnection.ERROR_INVALID_PARAMETER = 41
* IPConnection.ERROR_FUNCTION_NOT_SUPPORTED = 42
* IPConnection.ERROR_UNKNOWN_ERROR = 43

The namespace for the JavaScript bindings is ``Tinkerforge.*``.

{1}

{2}
""",
        'de': """
{0}
API
---

Alle folgend aufgelisteten Funktionen sind Thread-sicher.

{1}

{2}
"""
        }

        const_str = {
        'en' : """
.. _{4}_{5}_javascript_constants:

Constants
^^^^^^^^^

.. javascript:attribute:: {0}.DEVICE_IDENTIFIER

 This constant is used to identify a {2} {3}.

 The :javascript:func:`getIdentity() <{0}.getIdentity>` function and the
 :javascript:attr:`CALLBACK_ENUMERATE <IPConnection.CALLBACK_ENUMERATE>`
 callback of the IP Connection have a ``device_identifier`` parameter to specify
 the Brick's or Bricklet's type.
""",
        'de' : """
.. _{4}_{5}_javascript_constants:

Konstanten
^^^^^^^^^^

.. javascript:attribute:: {0}.DEVICE_IDENTIFIER

 Diese Konstante wird verwendet um {1} {2} {3} zu identifizieren.

 Die :javascript:func:`getIdentity() <{0}.getIdentity>` Funktion und der
 :javascript:attr:`CALLBACK_ENUMERATE <IPConnection.CALLBACK_ENUMERATE>`
 Callback der IP Connection haben ein ``device_identifier`` Parameter um den Typ
 des Bricks oder Bricklets anzugeben.
"""
        }

        cre = common.select_lang(create_str).format(self.get_underscore_name(),
                                                    self.get_javascript_class_name(),
                                                    self.get_category().lower(),
                                                    self.get_headless_camel_case_name())
        reg = common.select_lang(register_str).format(self.get_underscore_name(),
                                                      self.get_javascript_class_name(),
                                                      self.get_category().lower())

        bf = self.get_javascript_methods('bf')
        af = self.get_javascript_methods('af')
        ccf = self.get_javascript_methods('ccf')
        c = self.get_javascript_callbacks()
        api_str = ''
        if bf:
            api_str += common.select_lang(common.bf_str).format(cre, bf)
        if af:
            api_str += common.select_lang(common.af_str).format(af)
        if c:
            api_str += common.select_lang(common.ccf_str).format(reg, ccf)
            api_str += common.select_lang(c_str).format(c, self.get_underscore_name(),
                                                        self.get_category().lower(),
                                                        self.get_javascript_class_name(),
                                                        self.get_headless_camel_case_name())

        article = 'ein'
        if self.get_category() == 'Brick':
            article = 'einen'
        api_str += common.select_lang(const_str).format(self.get_javascript_class_name(),
                                                        article,
                                                        self.get_display_name(),
                                                        self.get_category(),
                                                        self.get_underscore_name(),
                                                        self.get_category().lower())

        ref = '.. _{0}_{1}_javascript_api:\n'.format(self.get_underscore_name(),
                                                 self.get_category().lower())

        return common.select_lang(api).format(ref, self.get_api_doc(), api_str)

    def get_javascript_doc(self):
        title = { 'en': 'JavaScript bindings', 'de': 'JavaScript Bindings' }

        doc  = common.make_rst_header(self, 'JavaScript')
        doc += common.make_rst_summary(self, common.select_lang(title))
        doc += self.get_javascript_examples()
        doc += self.get_javascript_api()

        return doc

class JavaScriptDocPacket(javascript_common.JavaScriptPacket):
    def get_javascript_formatted_doc(self):
        text = common.select_lang(self.get_doc()[1])
        cls = self.get_device().get_javascript_class_name()
        for other_packet in self.get_device().get_packets():
            name_false = ':func:`{0}`'.format(other_packet.get_camel_case_name())
            if other_packet.get_type() == 'callback':
                name_upper = other_packet.get_upper_case_name()
                name_right = ':javascript:attr:`CALLBACK_{1} <{0}.CALLBACK_{1}>`'.format(cls, name_upper)
            else:
                name_right = ':javascript:func:`{1}() <{0}.{1}>`'.format(cls, other_packet.get_headless_camel_case_name())
            text = text.replace(name_false, name_right)

        def format_parameter(name):
            return '``{0}``'.format(name) # FIXME

        text = common.handle_rst_param(text, format_parameter)
        text = common.handle_rst_word(text)
        text = common.handle_rst_substitutions(text, self)

        prefix = self.get_device().get_javascript_class_name() + '.'
        if self.get_underscore_name() == 'set_response_expected':
            text += common.format_function_id_constants(prefix, self.get_device())
        else:
            text += common.format_constants(prefix, self)

        text += common.format_since_firmware(self.get_device(), self)

        return common.shift_right(text, 1)

    def get_javascript_parameter_desc(self, io):
        desc = '\n'
        param = ' :param {0}: {1}\n'
        for element in self.get_elements(io):
            t = element.get_javascript_type()
            desc += param.format(element.get_headless_camel_case_name(), t)

        return desc

    def get_javascript_return_desc(self):
        desc = []
        param = ' :return {0}: {1}'
        for element in self.get_elements('out'):
            t = element.get_javascript_type()
            desc.append(param.format(element.get_headless_camel_case_name(), t))

        if len(desc) == 0:
            return '\n :noreturn: undefined\n'

        return '\n' + '\n'.join(desc) + '\n'

class JavaScriptDocGenerator(common.DocGenerator):
    def get_bindings_name(self):
        return 'javascript'

    def get_device_class(self):
        return JavaScriptDocDevice

    def get_packet_class(self):
        return JavaScriptDocPacket

    def get_element_class(self):
        return javascript_common.JavaScriptElement

    def generate(self, device):
        filename = '{0}_{1}_JavaScript.rst'.format(device.get_camel_case_name(), device.get_category())

        rst = open(os.path.join(self.get_bindings_root_directory(), 'doc', common.lang, filename), 'wb')
        rst.write(device.get_javascript_doc())
        rst.close()

def generate(bindings_root_directory, language):
    common.generate(bindings_root_directory, language, JavaScriptDocGenerator)

if __name__ == "__main__":
    for language in ['en', 'de']:
        print("=== Generating %s ===" % language)
        generate(os.getcwd(), language)
