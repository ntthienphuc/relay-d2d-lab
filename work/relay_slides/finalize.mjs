import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const root=path.resolve('../..');
const skill='C:/Users/thien/.codex/plugins/cache/openai-primary-runtime/presentations/26.1119.11507/skills/presentations';
const runtime='C:/Program Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1119-907-0_26.1119.907.0_x64__3k8sg7r9htsxt/dependencies';
process.env.RUNTIME_NODE_MODULES=path.join(runtime,'node/node_modules');
process.env.RUNTIME_NODE=path.join(runtime,'node/bin/node.exe');
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')));
const m=JSON.parse(await fs.readFile('deck_manifest.json','utf8'));
const result=await finalizePresentation({workspaceDir:root,candidatePath:path.resolve('candidate.pptx'),finalPath:path.join(root,'outputs/relay_presentation/Relay_D2D_Thuyet_trinh.pptx'),
 pythonExecutable:path.join(runtime,'python/python.exe'),integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...m.nativeTableSlides.flatMap(x=>['--require-native-table-slide',String(x)])],
 explicitTotalSlideCount:30,requiredNativeTableOwnerSlides:m.nativeTableSlides,requiredNativeChartOwnerSlides:m.nativeChartSlides,materializeLiteralChartWorkbooks:true,
 fontPolicy:{basis:'design',families:['Arial','Consolas']},verifyArtifactToolImport:true,receiptPath:path.resolve('validation.json')});
console.log(JSON.stringify(result));
