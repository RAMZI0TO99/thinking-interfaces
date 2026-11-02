"""Synthetic decoder test sources; execution requires separate local admission.

No provider queries, filesystem writes, subprocesses or positive boundary claims.
All tampered XML/templates receive new correct byte/hash pins unless testing pins.
"""
import copy
import hashlib
import importlib.util
from pathlib import Path
import unittest
from xml.sax.saxutils import escape, quoteattr


spec = importlib.util.spec_from_file_location("_provider_decoder_v4_tests", Path(__file__).with_name("decoder.py"))
decoder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(decoder)
NS = "http://schemas.microsoft.com/win/2004/08/events"
WIN_NS = "http://manifests.microsoft.com/win/2004/08/windows/events"
PROVIDER = "Microsoft-Windows-Kernel-Boot"
GUID = "11111111-2222-4333-8444-555555555555"
FALSE_FIELDS = ("boundary_qualified", "host_association_authenticated", "launch_authorized", "scientific_admission")


def pin(text):
    raw = text.encode("utf-8")
    return {"xml": text, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def query(**updates):
    result = {"key": "boot", "provider": PROVIDER, "channel": "System", "event_ids": [27],
              "from_utc": "2026-10-27T17:05:08.2987118Z", "to_utc": "2026-10-29T00:00:00Z"}
    result.update(updates)
    return result


def event_xml(*, provider=PROVIDER, guid=GUID, event_id="27", version="0", record_id="42",
              timestamp="2026-10-28T12:34:56.123456789Z", channel="System", computer="SYNTHETIC-HOST",
              data=None, data_xml=None, extra_system="", extra_sections=""):
    identity = ' Name=' + quoteattr(provider)
    if guid is not None:
        identity += ' Guid=' + quoteattr("{" + guid + "}")
    if data_xml is None:
        if data is None:
            data = [("BootType", "0")]
        data_xml = "".join("<Data Name=" + quoteattr(name) + ">" + escape(value) + "</Data>" for name, value in data)
    return ('<Event xmlns="' + NS + '"><System><Provider' + identity + '/>'
            '<EventID>' + event_id + '</EventID><Version>' + version + '</Version>'
            '<Level>4</Level><Task>20</Task><Opcode>0</Opcode><Keywords>0x8000000000000000</Keywords>'
            '<TimeCreated SystemTime=' + quoteattr(timestamp) + '/><EventRecordID>' + record_id + '</EventRecordID>'
            '<Correlation/><Execution ProcessID="4" ThreadID="8"/><Channel>' + escape(channel) + '</Channel>'
            '<Computer>' + escape(computer) + '</Computer><Security UserID="S-1-5-18"/>' + extra_system
            + '</System><EventData>' + data_xml + '</EventData>' + extra_sections + '</Event>')


def metadata(fields=None, *, template_xml=None, provider=PROVIDER, guid=GUID, event_id=27, version=0):
    if template_xml is None:
        if fields is None:
            fields = [("BootType", "win:UInt32")]
        template_xml = '<template xmlns="' + NS + '" xmlns:win="' + WIN_NS + '" tid="Synthetic">' + "".join(
            '<data name=' + quoteattr(name) + ' inType=' + quoteattr(kind) + '/>' for name, kind in fields) + '</template>'
    return {"provider": provider, "guid": guid,
            "definitions": [{"event_id": event_id, "version": version, "template": pin(template_xml)}],
            "exhausted": True, "truncated": False, "errors": []}


class UTCDecoderTests(unittest.TestCase):
    def test_fractional_digits_are_lossless(self):
        base = decoder.utc_ns("2026-10-28T12:34:56Z")
        self.assertEqual(decoder.utc_ns("2026-10-28T12:34:56.123456789Z") - base, 123456789)
        self.assertEqual(decoder.utc_ns("2026-10-28T12:34:56.1Z") - base, 100000000)
        self.assertEqual(decoder.utc_ns("2026-10-28T12:34:56.000000001Z") - base, 1)

    def test_calendar_leap_and_epoch_values(self):
        self.assertEqual(decoder.utc_ns("1970-01-01T00:00:00Z"), 0)
        self.assertEqual(decoder.utc_ns("1969-12-31T23:59:59.999999999Z"), -1)
        self.assertEqual(decoder.utc_ns("2024-03-01T00:00:00Z") - decoder.utc_ns("2024-02-29T00:00:00Z"), 86400 * 10**9)

    def test_invalid_calendar_values_refused(self):
        for text in ("2026-02-29T00:00:00Z", "2026-04-31T00:00:00Z", "0000-01-01T00:00:00Z",
                     "2026-10-28T24:00:00Z", "2026-10-28T23:59:60Z", "2026-13-01T00:00:00Z"):
            with self.subTest(text=text), self.assertRaises(decoder.DecodeError):
                decoder.utc_ns(text)

    def test_utc_offsets_noncanonical_and_precision_refused(self):
        for text in (None, 0, True, "2026-10-28T12:34:56+00:00", "2026-10-28t12:34:56Z",
                     "2026-10-28T12:34:56.1234567890Z", "2026-10-28T12:34:56.Z", "2026-10-28T12:34:56Z "):
            with self.subTest(text=text), self.assertRaises(decoder.DecodeError):
                decoder.utc_ns(text)


class EventDecoderTests(unittest.TestCase):
    def decode(self, text=None, selected=None):
        return decoder.decode_event(pin(event_xml() if text is None else text), query() if selected is None else selected)

    def test_selected_event_preserves_pins_identity_time_and_false_authority(self):
        row = pin(event_xml())
        result = decoder.decode_event(row, query())
        self.assertEqual(result["raw"], {key: row[key] for key in ("bytes", "sha256")})
        self.assertEqual((result["provider_name"], result["provider_guid"], result["event_id"], result["version"], result["record_id"]),
                         (PROVIDER, GUID, 27, 0, 42))
        self.assertEqual(result["timestamp_ns"], decoder.utc_ns(result["timestamp_utc"]))
        self.assertEqual(result["data"], {"BootType": "0"})
        self.assertEqual(result["computer_label_sha256"], hashlib.sha256(b"SYNTHETIC-HOST").hexdigest())
        for key in FALSE_FIELDS:
            self.assertIs(result[key], False)

    def test_raw_pin_fields_types_lengths_and_digest(self):
        good = pin(event_xml())
        bad = [None, [], dict(good, extra=True), dict(good, bytes=True), dict(good, bytes=good["bytes"] + 1),
               dict(good, sha256="0" * 64), dict(good, sha256=good["sha256"].upper()), dict(good, xml=b"not text")]
        for value in bad:
            with self.subTest(value=value), self.assertRaises(decoder.DecodeError):
                decoder.decode_event(value, query())

    def test_utf8_bytes_and_escaped_scalar_are_exact(self):
        value = "μ & <label>"
        text = event_xml(data=[("Text", value)], computer="SYNTHETIC-μ")
        self.assertGreater(pin(text)["bytes"], len(text))
        self.assertEqual(self.decode(text)["data"]["Text"], value)

    def test_raw_byte_and_scalar_bounds(self):
        for text in (" " * (decoder.MAX_XML_BYTES + 1), event_xml(data=[("Text", "A" * 4097)])):
            with self.subTest(length=len(text)), self.assertRaises(decoder.DecodeError):
                self.decode(text)
        bad = {"xml": "\ud800", "bytes": 1, "sha256": "0" * 64}
        with self.assertRaises(decoder.DecodeError):
            decoder.decode_event(bad, query())

    def test_dtd_entities_comments_pi_and_cdata_refused(self):
        text = event_xml()
        variants = ["<!DOCTYPE Event [<!ENTITY x 'x'>]>" + text, "<!--comment-->" + text,
                    "<?xml version='1.0'?>" + text, text.replace("<Data Name=", "<?target value?><Data Name="),
                    text.replace(">0</Data>", "><![CDATA[0]]></Data>")]
        for value in variants:
            with self.subTest(value=value[:60]), self.assertRaises(decoder.DecodeError):
                self.decode(value)

    def test_xml_namespace_root_and_trailing_document_refused(self):
        text = event_xml()
        variants = [text.replace(NS, "urn:wrong"), text.replace("<Event xmlns", "<Other xmlns", 1).replace("</Event>", "</Other>"),
                    text + text, text.replace("<EventData>", '<EventData xmlns="urn:wrong">')]
        for value in variants:
            with self.subTest(value=value[:60]), self.assertRaises(decoder.DecodeError):
                self.decode(value)

    def test_duplicate_sections_system_fields_and_required_fields(self):
        text = event_xml()
        variants = [text.replace("</System>", "<Version>0</Version></System>"),
                    text.replace("<EventData>", "<System/><EventData>"),
                    text.replace("</Event>", "<EventData/></Event>"), text.replace("<Version>0</Version>", ""),
                    text.replace("<Channel>System</Channel>", "")]
        for value in variants:
            with self.subTest(value=value[:60]), self.assertRaises(decoder.DecodeError):
                self.decode(value)

    def test_system_unknown_attributes_nested_scalar_and_mixed_text(self):
        text = event_xml()
        variants = [event_xml(extra_system="<UnqualifiedIdentity>true</UnqualifiedIdentity>"),
                    text.replace("<Level>", '<Level extra="x">'), text.replace("<Computer>SYNTHETIC-HOST", "<Computer><x/>SYNTHETIC-HOST"),
                    text.replace("<System>", "<System>mixed"), text.replace("</Version>", "</Version>mixed")]
        for value in variants:
            with self.subTest(value=value[:60]), self.assertRaises(decoder.DecodeError):
                self.decode(value)

    def test_xml_depth_node_and_attribute_bounds(self):
        variants = [event_xml(data_xml="<Data Name='X'>" + "<x>" * 17 + "0" + "</x>" * 17 + "</Data>"),
                    event_xml(data=[("F" + str(index), "") for index in range(1025)]),
                    event_xml(provider="A" * 4097)]
        for value in variants:
            with self.subTest(length=len(value)), self.assertRaises(decoder.DecodeError):
                self.decode(value)

    def test_event_identity_integer_types_and_ranges(self):
        for key, values in {"event_id": ["027", "-1", "65536", "0x1b"], "version": ["00", "256", "true"],
                            "record_id": ["01", "-1", str(2**64)]}.items():
            for value in values:
                with self.subTest(key=key, value=value), self.assertRaises(decoder.DecodeError):
                    self.decode(event_xml(**{key: value}))

    def test_query_provider_channel_event_and_time_constraints(self):
        bad = [query(provider="Other"), query(channel="Security"), query(event_ids=[12]),
               query(from_utc="2026-10-29T00:00:00Z", to_utc="2026-10-30T00:00:00Z"),
               query(to_utc="2026-10-28T00:00:00Z")]
        for selected in bad:
            with self.subTest(selected=selected), self.assertRaises(decoder.DecodeError):
                self.decode(selected=selected)

    def test_query_malformed_ids_identity_and_reversed_window(self):
        bad = [None, {}, query(event_ids=[True]), query(event_ids=[27, 27]), query(event_ids=[]),
               query(event_ids=[65536]), query(key=False), query(provider=""),
               query(from_utc="2026-10-30T00:00:00Z", to_utc="2026-10-29T00:00:00Z")]
        for selected in bad:
            with self.subTest(selected=selected), self.assertRaises(decoder.DecodeError):
                decoder.decode_event(pin(event_xml()), selected)

    def test_time_window_edges_are_inclusive_without_rounding(self):
        stamp = "2026-10-28T12:34:56.123456789Z"
        selected = query(from_utc=stamp, to_utc=stamp)
        self.decode(selected=selected)
        for shifted in ("2026-10-28T12:34:56.123456788Z", "2026-10-28T12:34:56.123456790Z"):
            with self.subTest(stamp=shifted), self.assertRaises(decoder.DecodeError):
                self.decode(event_xml(timestamp=shifted), selected)

    def test_data_duplicate_case_alias_unnamed_nested_and_userdata_refused(self):
        variants = [event_xml(data=[("BootType", "0"), ("BootType", "1")]),
                    event_xml(data=[("BootType", "0"), ("boottype", "1")]),
                    event_xml(data_xml="<Data>unnamed</Data>"), event_xml(data_xml="<Data Name='X'><nested/></Data>"),
                    event_xml(extra_sections="<UserData/>"), event_xml(extra_sections="<RenderingInfo/>")]
        for text in variants:
            with self.subTest(text=text[-100:]), self.assertRaises(decoder.DecodeError):
                self.decode(text)

    def test_guid_validation_and_missing_guid_cannot_match(self):
        self.assertEqual(self.decode(event_xml(guid=GUID.upper()))["provider_guid"], GUID)
        for value in ("not-guid", "0" * 32):
            with self.subTest(value=value), self.assertRaises(decoder.DecodeError):
                self.decode(event_xml(guid=value))
        event = self.decode(event_xml(guid=None))
        self.assertIsNone(event["provider_guid"])
        self.assertEqual(decoder.qualify_event(event, metadata())["status"], "UNSUPPORTED")

    def test_optional_system_attribute_values_are_checked(self):
        text = event_xml()
        for source, replacement in (("ProcessID=\"4\"", "ProcessID=\"-1\""),
                                    ("UserID=\"S-1-5-18\"", "UserID=\"S-1-5-4294967296\""),
                                    ("<Correlation/>", "<Correlation ActivityID='not-guid'/>"),
                                    ("<Keywords>0x8000000000000000</Keywords>", "<Keywords>0x10000000000000000</Keywords>")):
            with self.subTest(replacement=replacement), self.assertRaises(decoder.DecodeError):
                self.decode(text.replace(source, replacement))

    def test_historical_security_pid_spellings_remain_candidates(self):
        name = "Microsoft-Windows-Security-Auditing"
        values = ["0x49c2c", "0x49C2C", "0X49C2C"]
        selected = query(key="historical_creation", provider=name, channel="Security", event_ids=[4688], pid_hex_values=values)
        for value in values:
            event = self.decode(event_xml(provider=name, event_id="4688", channel="Security", data=[("NewProcessId", value)]), selected)
            self.assertEqual(event["data"]["NewProcessId"], value)
            for flag in FALSE_FIELDS:
                self.assertIs(event[flag], False)

    def test_historical_pid_wrong_value_spelling_or_event_family_refused(self):
        name = "Microsoft-Windows-Security-Auditing"
        selected = query(provider=name, channel="Security", event_ids=[4688], pid_hex_values=["0x49c2c"])
        for value in ("0x49c2d", "302124", "0x49C2C"):
            with self.subTest(value=value), self.assertRaises(decoder.DecodeError):
                self.decode(event_xml(provider=name, event_id="4688", channel="Security", data=[("NewProcessId", value)]), selected)
        with self.assertRaises(decoder.DecodeError):
            self.decode(selected=query(pid_hex_values=["0x49c2c"]))
        with self.assertRaises(decoder.DecodeError):
            self.decode(event_xml(provider=name, event_id="4688", channel="Security", data=[("NewProcessId", "0x49c2c")]),
                        dict(selected, pid_hex_values=["0x49c2d"]))


class TemplateQualificationTests(unittest.TestCase):
    def event(self, data=None):
        return decoder.decode_event(pin(event_xml(data=data)), query())

    def match(self, data=None, fields=None, **updates):
        return decoder.qualify_event(self.event(data), metadata(fields, **updates))

    def test_boot_type_zero_match_never_grants_restart_or_host_authority(self):
        result = self.match()
        self.assertEqual(result["status"], "MATCHED_LOCAL_TEMPLATE")
        self.assertEqual(result["typed_data"], {"BootType": 0})
        for flag in FALSE_FIELDS:
            self.assertIs(result[flag], False)
        self.assertNotIn("restart_qualified", result)

    def test_missing_mismatched_provider_guid_and_version_unsupported(self):
        for record in (metadata(provider="Other"), metadata(guid="aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"),
                       metadata(version=1), metadata(event_id=12), metadata(guid=None)):
            with self.subTest(record=record):
                self.assertEqual(decoder.qualify_event(self.event(), record)["status"], "UNSUPPORTED")

    def test_definition_duplicates_unknown_fields_types_and_bound(self):
        good = metadata()
        duplicate = copy.deepcopy(good)
        duplicate["definitions"].append(copy.deepcopy(duplicate["definitions"][0]))
        unknown = copy.deepcopy(good)
        unknown["definitions"][0]["trusted"] = True
        boolean = copy.deepcopy(good)
        boolean["definitions"][0]["version"] = False
        for record in (duplicate, unknown, boolean, dict(good, definitions=[good["definitions"][0]] * 257)):
            with self.subTest(record=record):
                self.assertEqual(decoder.qualify_event(self.event(), record)["status"], "UNSUPPORTED")

    def test_template_pin_malformed_xml_namespace_and_directives(self):
        good = metadata()
        bad_pin = copy.deepcopy(good)
        bad_pin["definitions"][0]["template"]["sha256"] = "0" * 64
        self.assertEqual(decoder.qualify_event(self.event(), bad_pin)["status"], "UNSUPPORTED")
        for xml in ("", "<template>", "<template/>", '<template xmlns="urn:wrong"/>', "<!DOCTYPE template><template/>"):
            with self.subTest(xml=xml):
                self.assertEqual(self.match(template_xml=xml)["status"], "UNSUPPORTED")

    def test_template_field_names_order_exact_and_case_sensitive(self):
        for fields in ([('Other', 'win:UInt32')], [('boottype', 'win:UInt32')],
                       [('BootType', 'win:UInt32'), ('Extra', 'win:UInt32')]):
            with self.subTest(fields=fields):
                self.assertEqual(self.match(fields=fields)["status"], "UNSUPPORTED")
        self.assertEqual(self.match(data=[('B', '1'), ('A', '2')], fields=[('A', 'win:UInt32'), ('B', 'win:UInt32')])["status"], "UNSUPPORTED")

    def test_template_struct_array_length_alias_and_duplicate_refused(self):
        fragments = ["<struct name='BootType'/>", "<data name='BootType' inType='win:UInt32' count='1'/>",
                     "<data name='BootType' inType='win:UInt32' length='4'/>",
                     "<data name='BootType' inType='win:UInt32'/><data name='BootType' inType='win:UInt32'/>",
                     "<data name='BootType' inType='win:UInt32'/><data name='boottype' inType='win:UInt32'/>"
                     ]
        for fragment in fragments:
            with self.subTest(fragment=fragment):
                xml = '<template xmlns="' + NS + '" xmlns:win="' + WIN_NS + '">' + fragment + '</template>'
                self.assertEqual(self.match(template_xml=xml)["status"], "UNSUPPORTED")

    def test_unsigned_width_limits_decimal_and_hex(self):
        for width in (8, 16, 32, 64):
            kind = "win:UInt" + str(width)
            for text in (str(2**width - 1), hex(2**width - 1)):
                with self.subTest(kind=kind, text=text):
                    result = self.match(data=[('X', text)], fields=[('X', kind)])
                    self.assertEqual(result["typed_data"]["X"], 2**width - 1)
            for text in (str(2**width), "-1", "01", "1.0", "true"):
                with self.subTest(kind=kind, text=text):
                    self.assertEqual(self.match(data=[('X', text)], fields=[('X', kind)])["status"], "UNSUPPORTED")

    def test_signed_width_limits_and_canonical_spelling(self):
        for width in (8, 16, 32, 64):
            kind = "win:Int" + str(width)
            for value in (-(2**(width - 1)), 2**(width - 1) - 1):
                with self.subTest(kind=kind, value=value):
                    self.assertEqual(self.match(data=[('X', str(value))], fields=[('X', kind)])["typed_data"]["X"], value)
            for text in (str(2**(width - 1)), str(-(2**(width - 1)) - 1), "-0", "+1", "01"):
                with self.subTest(kind=kind, text=text):
                    self.assertEqual(self.match(data=[('X', text)], fields=[('X', kind)])["status"], "UNSUPPORTED")

    def test_hex_pointer_boolean_representations(self):
        for kind in ('win:HexInt32', 'win:HexInt64', 'win:Pointer'):
            with self.subTest(kind=kind):
                self.assertEqual(self.match(data=[('X', '0Xf')], fields=[('X', kind)])["typed_data"]["X"], 15)
                self.assertEqual(self.match(data=[('X', '15')], fields=[('X', kind)])["status"], "UNSUPPORTED")
        for text, value in (('true', True), ('false', False), ('1', True), ('0', False)):
            self.assertIs(self.match(data=[('X', text)], fields=[('X', 'win:Boolean')])["typed_data"]["X"], value)
        self.assertEqual(self.match(data=[('X', 'TRUE')], fields=[('X', 'win:Boolean')])["status"], "UNSUPPORTED")

    def test_guid_sid_filetime_and_unicode_scalar_types(self):
        fields = [('G', 'win:GUID'), ('S', 'win:SID'), ('T', 'win:FILETIME'), ('U', 'win:UnicodeString')]
        text = '2026-10-28T12:34:56.000000001Z'
        result = self.match(data=[('G', '{' + GUID.upper() + '}'), ('S', 'S-1-5-18'), ('T', text), ('U', 'μ & text')], fields=fields)
        self.assertEqual(result['typed_data'], {'G': GUID, 'S': 'S-1-5-18', 'T': decoder.utc_ns(text), 'U': 'μ & text'})
        for kind, value in (('win:GUID', 'bad'), ('win:SID', 'S-1-5-4294967296'), ('win:FILETIME', '2026-02-29T00:00:00Z')):
            self.assertEqual(self.match(data=[('X', value)], fields=[('X', kind)])["status"], "UNSUPPORTED")

    def test_unknown_template_types_and_output_annotations_cannot_authorize(self):
        for kind in ('win:Binary', 'win:Double', 'evil:UInt32', 'UInt32'):
            self.assertEqual(self.match(fields=[('BootType', kind)])["status"], "UNSUPPORTED")
        xml = '<template xmlns="' + NS + '" xmlns:win="' + WIN_NS + '"><data name="BootType" inType="win:UInt32" outType="win:HexInt32"/></template>'
        result = self.match(template_xml=xml)
        self.assertEqual(result["status"], "MATCHED_LOCAL_TEMPLATE")
        self.assertIs(result["boundary_qualified"], False)

    def test_template_qnames_require_correct_element_scope_namespace(self):
        template = metadata()["definitions"][0]["template"]["xml"]
        variants = [template.replace(WIN_NS, "urn:untrusted"),
                    template.replace(' xmlns:win="' + WIN_NS + '"', ""),
                    template.replace('<data ', '<data xmlns:win="urn:untrusted" '),
                    template.replace('inType="win:UInt32"', 'inType="other:UInt32"'),
                    template.replace('inType="win:UInt32"', 'inType="win:UInt32" outType="other:HexInt32"')]
        for xml in variants:
            with self.subTest(xml=xml):
                self.assertEqual(self.match(template_xml=xml)["status"], "UNSUPPORTED")
        # A declaration local to the used data element is valid in that scope.
        local = template.replace(' xmlns:win="' + WIN_NS + '"', "").replace('<data ', '<data xmlns:win="' + WIN_NS + '" ')
        self.assertEqual(self.match(template_xml=local)["status"], "MATCHED_LOCAL_TEMPLATE")
        # A later sibling's declaration cannot bind an earlier sibling's QName.
        sibling = ('<template xmlns="' + NS + '"><data name="A" inType="win:UInt32"/>'
                   '<data xmlns:win="' + WIN_NS + '" name="B" inType="win:UInt32"/></template>')
        self.assertEqual(self.match(data=[('A', '1'), ('B', '2')], template_xml=sibling)["status"], "UNSUPPORTED")

    def test_template_namespace_declaration_budget_is_bounded(self):
        declarations = " ".join('xmlns:p' + str(i) + '="urn:p' + str(i) + '"' for i in range(15))
        xml = metadata()["definitions"][0]["template"]["xml"].replace(' tid="Synthetic"', ' ' + declarations)
        self.assertEqual(self.match(template_xml=xml)["status"], "UNSUPPORTED")

    def test_forged_decoded_authority_and_malformed_record_refused(self):
        for flag in FALSE_FIELDS:
            event = self.event()
            event[flag] = True
            result = decoder.qualify_event(event, metadata())
            self.assertEqual(result["status"], "UNSUPPORTED")
            for returned_flag in FALSE_FIELDS:
                self.assertIs(result[returned_flag], False)
        for event, record in ((None, metadata()), (self.event(), None), ({}, metadata()),
                              (dict(self.event(), event_id=True), metadata()), (dict(self.event(), data=[]), metadata())):
            with self.subTest(event=event, record=record):
                self.assertEqual(decoder.qualify_event(event, record)["status"], "UNSUPPORTED")

    def test_template_hash_and_payload_order_are_bound_without_input_mutation(self):
        event, record = self.event(), metadata()
        originals = copy.deepcopy((event, record))
        result = decoder.qualify_event(event, record)
        self.assertEqual(result["template"], {key: record["definitions"][0]["template"][key] for key in ("bytes", "sha256")})
        self.assertEqual((event, record), originals)
        self.assertIsNot(event["data"], result["typed_data"])


if __name__ == "__main__":
    unittest.main()
