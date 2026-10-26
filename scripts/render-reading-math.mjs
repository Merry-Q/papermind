// Native MathML output keeps standalone editions independent of font/CDN requests.
import katex from '../frontend/node_modules/katex/dist/katex.mjs';
let input='';for await(const chunk of process.stdin)input+=chunk;
const expressions=JSON.parse(input);
process.stdout.write(JSON.stringify(expressions.map(tex=>katex.renderToString(tex,{output:'mathml',throwOnError:false,trust:false,strict:'ignore'}))));
