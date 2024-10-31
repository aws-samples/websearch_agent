from typing import cast

from aws_cdk import Aws, BundlingOptions, BundlingOutput, DockerImage, RemovalPolicy
from aws_cdk import aws_lambda as _lambda
from aws_cdk.aws_opsworks import CfnLayer
from aws_cdk.aws_s3_assets import Asset
from constructs import Construct

# THE VERSION OF POWERTOOLS arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-{python_version}-arm64:2 with python version being python312 e.g.
# from https://docs.powertools.aws.dev/lambda/python/latest/#lambda-layer

AWS_LAMBDA_POWERTOOL_LAYER_VERSION_ARN = "arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-{python_version}-arm64:2"


class WebSearchLambdaLayers(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        stack_name: str,
        architecture: _lambda.Architecture,
        python_runtime: _lambda.Runtime = _lambda.Runtime.PYTHON_3_12,
        region: str = Aws.REGION,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self._runtime = python_runtime
        self._architecture = architecture
        self._region = region
        self._python_handle = self._runtime.name.replace(".", "")
        # print(self._python_handle)

        # print(self._region)
        # print(
        #     AWS_LAMBDA_POWERTOOL_LAYER_VERSION_ARN.format(
        #         region=self._region, python_version=self._python_handle
        #     ),
        # )
        # AWS Lambda PowerTools
        self.aws_lambda_powertools = _lambda.LayerVersion.from_layer_version_arn(
            self,
            f"{stack_name}-lambda-powertools-layer",
            layer_version_arn=AWS_LAMBDA_POWERTOOL_LAYER_VERSION_ARN.format(
                region=self._region, python_version=self._python_handle
            ),
        )

        # Project dependencies layer
        self.project_dependencies = self._create_layer_from_asset(
            layer_name=f"{stack_name}-project-dependencies-layer",
            path_to_layer_assets="lambda_layer/advanced_websearch_libraries",
            description="Lambda layer containing project dependencies (aiohttp, pydantic, langchain)",
        )

    def _create_layer_from_asset(
        self, layer_name: str, path_to_layer_assets: str, description: str
    ) -> _lambda.LayerVersion:
        ecr = (
            self._runtime.bundling_image.image
            + f":latest-{self._architecture.to_string()}"
        )
        bundling_option = BundlingOptions(
            image=DockerImage(ecr),
            command=[
                "bash",
                "-c",
                "pip --no-cache-dir install -r requirements.txt -t /asset-output/python",
            ],
            output_type=BundlingOutput.AUTO_DISCOVER,
            platform=self._architecture.docker_platform,
            network="host",
        )
        layer_asset = Asset(
            self,
            f"{layer_name}-BundledAsset",
            path=path_to_layer_assets,
            bundling=bundling_option,
        )
        layer_version = _lambda.LayerVersion(
            self,
            layer_name,
            code=_lambda.Code.from_bucket(
                layer_asset.bucket, layer_asset.s3_object_key
            ),
            compatible_runtimes=[self._runtime],
            compatible_architectures=[self._architecture],
            removal_policy=RemovalPolicy.DESTROY,
            layer_version_name=layer_name,
            description=description,
        )

        # Adding metadata entries to CF template for local testing
        cfn_layer = cast(CfnLayer, layer_version.node.default_child)
        layer_asset.add_resource_metadata(
            resource=cfn_layer, resource_property="Content"
        )
        return layer_version
