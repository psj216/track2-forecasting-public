"""Executive summary: official v2.6.1 parser controls, no team key and no pack."""
import json,pathlib,sys
from qfbench2_common.contracts.descriptor import SubmissionDescriptor,seal_descriptor_digest
root=pathlib.Path('/common-current/common/qfbench2_common');fixture=json.loads((root/'contracts/fixtures/c5/forecasting_final.json').read_text());schema=json.loads((root/'schemas/submission.schema.json').read_text())
SubmissionDescriptor.from_mapping(fixture)
draft=json.loads(pathlib.Path('/audit05/descriptor-draft.json').read_text())
try:SubmissionDescriptor.from_mapping(draft)
except Exception as e:rejection=type(e).__name__
else:raise AssertionError('Unpublished/null descriptor unexpectedly accepted')
control=dict(fixture);control['models']=[];control['license']='MIT';control=seal_descriptor_digest(control);SubmissionDescriptor.from_mapping(control)
print(json.dumps({'executive_summary':'Published fixture/parser and model-free control validated; actual secret-free draft rejected as expected. No package generated.','toolkit_source':'03c50a0036aaf72675d353aef4c7c01ca86d1fcf','required_fields':schema['required'],'additional_properties':schema['additionalProperties'],'official_final_fixture_pass':True,'synthetic_model_free_control_pass':True,'draft_expected_rejection':rejection,'actual_descriptor_ready':False,'pack_executed':False,'team_key_accessed':False}))
