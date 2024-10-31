The following errors are in the deployment.

I have the original v1 deployed. I think this is the problem that many resources get the same name.

I want you to step through the cdk files and make sure that in the config the user either sets a new unique name, and if that is not the case, just add a 4 place UUID to the resources so that they are unique.
<cdk errors>
(cdk) ➜ v2 git:(implement_v2) ✗ cdk deploy
jsii.errors.JavaScriptError:
@jsii/kernel.SerializationError: Passed to parameter props of new aws-cdk-lib.aws_lambda.Function: Unable to deserialize value as aws-cdk-lib.aws_lambda.FunctionProps
├── 🛑 Failing value is an object
│ { '$jsii.struct': [Object] }
  ╰── 🔍 Failure reason(s):
      ╰─ Key 'environment': Unable to deserialize value as map<string> | undefined
          ├── 🛑 Failing value is an object
          │      { '$jsii.map': [Object] }
╰── 🔍 Failure reason(s):
╰─ Key 'CROSS_REGION_INFERENCE': Unable to deserialize value as string
├── 🛑 Failing value is a boolean
│ true
╰── 🔍 Failure reason(s):
╰─ Value is not a string
at Object.process (/private/var/folders/xv/9pdl21z15cg26j02ffhkr7v40000gr/T/tmpfm1pdqc8/lib/program.js:10485:19)
at Kernel.\_Kernel_toSandbox (/private/var/folders/xv/9pdl21z15cg26j02ffhkr7v40000gr/T/tmpfm1pdqc8/lib/program.js:9463:25)
at /private/var/folders/xv/9pdl21z15cg26j02ffhkr7v40000gr/T/tmpfm1pdqc8/lib/program.js:9479:38
at Array.map (<anonymous>)
at Kernel.\_Kernel_boxUnboxParameters (/private/var/folders/xv/9pdl21z15cg26j02ffhkr7v40000gr/T/tmpfm1pdqc8/lib/program.js:9479:23)
at Kernel.\_Kernel_toSandboxValues (/private/var/folders/xv/9pdl21z15cg26j02ffhkr7v40000gr/T/tmpfm1pdqc8/lib/program.js:9467:101)
at Kernel.\_Kernel_create (/private/var/folders/xv/9pdl21z15cg26j02ffhkr7v40000gr/T/tmpfm1pdqc8/lib/program.js:9127:115)
at Kernel.create (/private/var/folders/xv/9pdl21z15cg26j02ffhkr7v40000gr/T/tmpfm1pdqc8/lib/program.js:8798:93)
at KernelHost.processRequest (/private/var/folders/xv/9pdl21z15cg26j02ffhkr7v40000gr/T/tmpfm1pdqc8/lib/program.js:10715:36)
at KernelHost.run (/private/var/folders/xv/9pdl21z15cg26j02ffhkr7v40000gr/T/tmpfm1pdqc8/lib/program.js:10675:22)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
File "/Users/philikai/Developer/aws-samples-contributions/WebSearchAgents/websearch_agent_implementation_fork/v2/app.py", line 12, in <module>
WebSearchAgentStack(app, "WebSearchAgentStack-v2")
File "/Users/philikai/opt/anaconda3/envs/cdk/lib/python3.12/site-packages/jsii/\_runtime.py", line 118, in **call**
inst = super(JSIIMeta, cast(JSIIMeta, cls)).**call**(*args, \*\*kwargs)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/Users/philikai/Developer/aws-samples-contributions/WebSearchAgents/websearch_agent_implementation_fork/v2/cdk/cdk_stack.py", line 121, in **init**
websearch_lambda, advanced_web_search_lambda = create_lambda_functions(
^^^^^^^^^^^^^^^^^^^^^^^^
File "/Users/philikai/Developer/aws-samples-contributions/WebSearchAgents/websearch_agent_implementation_fork/v2/cdk/lambda_functions.py", line 36, in create_lambda_functions
advanced_web_search_lambda = \_lambda.Function(
^^^^^^^^^^^^^^^^^
File "/Users/philikai/opt/anaconda3/envs/cdk/lib/python3.12/site-packages/jsii/\_runtime.py", line 118, in **call**
inst = super(JSIIMeta, cast(JSIIMeta, cls)).**call**(*args, \*\*kwargs)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/Users/philikai/opt/anaconda3/envs/cdk/lib/python3.12/site-packages/aws_cdk/aws_lambda/**init**.py", line 27169, in **init**
jsii.create(self.**class**, self, [scope, id, props])
File "/Users/philikai/opt/anaconda3/envs/cdk/lib/python3.12/site-packages/jsii/\_kernel/**init**.py", line 334, in create
response = self.provider.create(
^^^^^^^^^^^^^^^^^^^^^
File "/Users/philikai/opt/anaconda3/envs/cdk/lib/python3.12/site-packages/jsii/\_kernel/providers/process.py", line 365, in create
return self.\_process.send(request, CreateResponse)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/Users/philikai/opt/anaconda3/envs/cdk/lib/python3.12/site-packages/jsii/\_kernel/providers/process.py", line 342, in send
raise RuntimeError(resp.error) from JavaScriptError(resp.stack)
RuntimeError: Passed to parameter props of new aws-cdk-lib.aws_lambda.Function: Unable to deserialize value as aws-cdk-lib.aws_lambda.FunctionProps
├── 🛑 Failing value is an object
│ { '$jsii.struct': [Object] }
╰── 🔍 Failure reason(s):
    ╰─ Key 'environment': Unable to deserialize value as map<string> | undefined
        ├── 🛑 Failing value is an object
        │      { '$jsii.map': [Object] }
╰── 🔍 Failure reason(s):
╰─ Key 'CROSS_REGION_INFERENCE': Unable to deserialize value as string
├── 🛑 Failing value is a boolean
│ true
╰── 🔍 Failure reason(s):
╰─ Value is not a string
Subprocess exited with error 1
</cdk errors>
