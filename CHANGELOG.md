# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.6](https://github.com/rtrentin73/carlos-the-architect/compare/v0.2.5...v0.2.6) (2026-01-26)


### Features

* Add admin ability to delete users ([e038f6e](https://github.com/rtrentin73/carlos-the-architect/commit/e038f6ee6ab7c6aec7635dd43d31c35915c5f4c4))
* Add admin ability to delete users ([2b92db7](https://github.com/rtrentin73/carlos-the-architect/commit/2b92db7b5e928ccb8e1e746fe50623d0a85898c1))

## [0.2.5](https://github.com/rtrentin73/carlos-the-architect/compare/v0.2.4...v0.2.5) (2026-01-26)


### Bug Fixes

* Improve error handling for registration and login failures ([b716e54](https://github.com/rtrentin73/carlos-the-architect/commit/b716e543e4a7895a516e4b6a8a2b995c912bb18d))
* Improve error handling for registration and login failures ([4c58b45](https://github.com/rtrentin73/carlos-the-architect/commit/4c58b456690f9223953430077f5e85d2f8ad3ae6))

## [0.2.4](https://github.com/rtrentin73/carlos-the-architect/compare/v0.2.3...v0.2.4) (2026-01-26)


### Features

* Add gzip compression for design history storage ([88d98f1](https://github.com/rtrentin73/carlos-the-architect/commit/88d98f1e57d25ac409110f51fea7e6789a02b715))


### Bug Fixes

* Add better logging and UI for design history debugging ([c4238f1](https://github.com/rtrentin73/carlos-the-architect/commit/c4238f1624eeecf74f57125488faf539c59879a0))
* Simplify Cosmos DB query and add more debugging for design history ([9c76100](https://github.com/rtrentin73/carlos-the-architect/commit/9c761004a02a89ceb5127d0dada1dbcc47cb6557))
* Truncate large fields to fit Cosmos DB 2MB document limit ([a180b29](https://github.com/rtrentin73/carlos-the-architect/commit/a180b292aa5722a329135dce785f9f6a8ea4ed81))

## [0.2.3](https://github.com/rtrentin73/carlos-the-architect/compare/v0.2.2...v0.2.3) (2026-01-26)


### Bug Fixes

* Fall back to text extraction when diagram extraction fails ([49b5490](https://github.com/rtrentin73/carlos-the-architect/commit/49b5490b4e64587de1ac7b6f3f743d7d25f5aa88))
* Prevent blank screen when uploading documents ([ac38090](https://github.com/rtrentin73/carlos-the-architect/commit/ac3809073391cec8c8d9348665a79a8ad67966a5))

## [0.2.2](https://github.com/rtrentin73/carlos-the-architect/compare/v0.2.1...v0.2.2) (2026-01-26)


### Features

* Add diagram extraction from uploaded documents ([0a7e7a5](https://github.com/rtrentin73/carlos-the-architect/commit/0a7e7a58f1845a57bd9018f9e3b20dae72bc805f))
* Add diagram extraction from uploaded documents ([af26745](https://github.com/rtrentin73/carlos-the-architect/commit/af26745a81119e84ba809c2c585eea2a35098e8f))
* Add GPT-4 Vision integration for diagram analysis ([f596945](https://github.com/rtrentin73/carlos-the-architect/commit/f596945d1ca4a8c3a0085ad10828826273fd98fb))
* Feed document context and diagram analysis into design generation ([4378236](https://github.com/rtrentin73/carlos-the-architect/commit/43782362e4e7d0f72c600f6c42fa412ffb6f0e71))


### Bug Fixes

* Add Pydantic validators to handle string-to-float parsing in cos… ([f7e1829](https://github.com/rtrentin73/carlos-the-architect/commit/f7e1829efa131503a45ed5e0b03db4cfa0497d11))
* Add Pydantic validators to handle string-to-float parsing in cost schemas ([dff73cc](https://github.com/rtrentin73/carlos-the-architect/commit/dff73cc0edaea383f72941eaf9c413a51dd1be5d))
* Remove unsupported enable_cross_partition_query param from async Cosmos DB client ([8325267](https://github.com/rtrentin73/carlos-the-architect/commit/832526774fcc865630a677f8a022c363cf32057e))
* Remove unsupported enable_cross_partition_query param from async… ([cfafd9b](https://github.com/rtrentin73/carlos-the-architect/commit/cfafd9b7b08de192f6ed8fb71b7312065bb81a46))

## [0.2.1](https://github.com/rtrentin73/carlos-the-architect/compare/v0.2.0...v0.2.1) (2026-01-26)


### Features

* Add admin dashboard with user management and audit log viewer ([ec678ac](https://github.com/rtrentin73/carlos-the-architect/commit/ec678ac8f5cc416e62e1f6b49bcf1f44bcbe5844))
* Add async document processing with background tasks ([c9253d5](https://github.com/rtrentin73/carlos-the-architect/commit/c9253d5d63269494fc5a0aa1c84fa558be9ab5e6))
* Add Azure AI Document Intelligence for image/PDF OCR support ([bbc388d](https://github.com/rtrentin73/carlos-the-architect/commit/bbc388d115ea65b029905a80d3fc591ea6870816))
* Add Azure AI Document Intelligence to Terraform infrastructure ([6fc43e9](https://github.com/rtrentin73/carlos-the-architect/commit/6fc43e999ff4e9eb31cfa949d96dd6c4096e03e1))
* Add Carlos image to login page ([9740139](https://github.com/rtrentin73/carlos-the-architect/commit/9740139b3f45ca6d4b57b0ed9c6ab90ae7a21fc7))
* Add click-to-expand for agent messages in stream view ([6039be0](https://github.com/rtrentin73/carlos-the-architect/commit/6039be0dc30c1ba4ea4ec1d5b92cf56ae7a51c4e))
* Add delete button to design history entries ([6b21ce3](https://github.com/rtrentin73/carlos-the-architect/commit/6b21ce38fac02b84df4cfc9de9045f63edd1e8c3))
* Add delete button to design history entries ([12443d9](https://github.com/rtrentin73/carlos-the-architect/commit/12443d9efeb9cc49fb5d6b17c7562cb155f7e394))
* Add deployment feedback loop with Azure Cosmos DB persistence ([8a357f2](https://github.com/rtrentin73/carlos-the-architect/commit/8a357f2a8de92e93a617a4b39500d30bb07df480))
* Add deployment feedback loop with Azure Cosmos DB persistence ([6075d14](https://github.com/rtrentin73/carlos-the-architect/commit/6075d147d6eb530968930ad1dbb855add7be5224))
* Add design pattern caching for instant responses ([5c47fe4](https://github.com/rtrentin73/carlos-the-architect/commit/5c47fe49315361f9157e4129fadbfd900971c2c5))
* Add document upload button to main App.jsx UI ([01f430c](https://github.com/rtrentin73/carlos-the-architect/commit/01f430c0ff92160d8e30525e88d1cfe4c5102f35))
* Add document upload for requirements ([d437a6e](https://github.com/rtrentin73/carlos-the-architect/commit/d437a6e1fb5a60de39e2b2771cd57e94027fb15b))
* Add document upload for requirements ([46c5a94](https://github.com/rtrentin73/carlos-the-architect/commit/46c5a949dcbe5c18ece64936979f23e2f60e0cf5))
* Add Feedback Dashboard UI for viewing deployment feedback ([ccba92a](https://github.com/rtrentin73/carlos-the-architect/commit/ccba92af9e584260b45502f59369c59cec984e2e))
* Add historical learning from deployment feedback ([c80a267](https://github.com/rtrentin73/carlos-the-architect/commit/c80a26703182f416f392db8c121928de415d3e25))
* Add interactive requirements gathering to frontend ([54f48eb](https://github.com/rtrentin73/carlos-the-architect/commit/54f48ebffe7f47664d7a96f1eee6c8f652a257f6))
* Add LLM connection pooling for improved performance ([877afa0](https://github.com/rtrentin73/carlos-the-architect/commit/877afa0b7b66b45be646e6b2d48eda747d94fb88))
* Add LLM connection pooling for improved performance ([3229345](https://github.com/rtrentin73/carlos-the-architect/commit/3229345934dd60e2c92a8e352ab9b3aed7a1e04c))
* Add missing Cosmos DB containers to Terraform ([94747cc](https://github.com/rtrentin73/carlos-the-architect/commit/94747ccc80a37fbe32c41aa1bb349f022216e413))
* Add OAuth authentication with Google and GitHub ([80ca132](https://github.com/rtrentin73/carlos-the-architect/commit/80ca132a37927a57a737b0bd2aac2071d37d3021))
* Add OAuth authentication with Google and GitHub ([dcebc44](https://github.com/rtrentin73/carlos-the-architect/commit/dcebc4435a8ba200bfeeacdf66eea24f33ee8757))
* Add persistent design history storage with Cosmos DB ([f518d5c](https://github.com/rtrentin73/carlos-the-architect/commit/f518d5cb7810ebf05a4c225e96b0761514bb96a6))
* Add persistent user storage with Cosmos DB ([dcc2387](https://github.com/rtrentin73/carlos-the-architect/commit/dcc2387622240a360b7bf8cdf771cac74fd5f1d9))
* Add production audit logging and compliance tracking ([7e28684](https://github.com/rtrentin73/carlos-the-architect/commit/7e286841c604dea5e2ecfb62b2944baf1b6d512e))
* Add rate limiting protection for API endpoints ([9e0e251](https://github.com/rtrentin73/carlos-the-architect/commit/9e0e25147847ff32ad270c7abbfd3b241ec58658))
* Add real-time requirements clarification flow ([14d94f9](https://github.com/rtrentin73/carlos-the-architect/commit/14d94f9035c3945dac365bffcc5bd1a58d192620))
* Add reference search for design citations with Tavily API ([657e9d0](https://github.com/rtrentin73/carlos-the-architect/commit/657e9d080c2545098b7b09be26d8aea16e7076c0))
* Add requirements gathering phase with Carlos and Ronei ([bdaab9a](https://github.com/rtrentin73/carlos-the-architect/commit/bdaab9a09acf01c94816909f7ba2b24bf18d608f))
* Add shaded Carlos background image to main content area ([3a9ae32](https://github.com/rtrentin73/carlos-the-architect/commit/3a9ae3241c16503dcc0314a364d2581bf8186d61))
* Add shaded Carlos background image to main content area ([9147659](https://github.com/rtrentin73/carlos-the-architect/commit/914765935aed713d0d6a3730fe96dc042c85afe5))
* Add streaming for Terraform code generation ([0d80f51](https://github.com/rtrentin73/carlos-the-architect/commit/0d80f51ff0172b4e9aaa3b3b88b750677e527a50))
* Add streaming to all agents for real-time token display ([662809c](https://github.com/rtrentin73/carlos-the-architect/commit/662809c1890fc058135752402743e63c265b49c3))
* Add structured JSON outputs for analyst agents ([546124a](https://github.com/rtrentin73/carlos-the-architect/commit/546124a5ac6bfb4dbf49dc5c0e91ae9e8f855e7c))
* Add Terraform validation feedback loop ([19177ba](https://github.com/rtrentin73/carlos-the-architect/commit/19177ba9642e7a8d8dc260f4167755ec84b6195a))
* Add Terraform validation feedback loop ([ea3314d](https://github.com/rtrentin73/carlos-the-architect/commit/ea3314dba33da59ba30189763399b40ef40c0839))
* Add Terraform validator agent and copy button for code ([8116a09](https://github.com/rtrentin73/carlos-the-architect/commit/8116a09cfca6bb5240f5d0756ca32a71e934cd3a))
* Add Terraform validator agent and copy button for code ([b1a5476](https://github.com/rtrentin73/carlos-the-architect/commit/b1a5476f8a211e17385747b0f4ddc214187b0cfb))
* Auto-deploy Redis credentials to Kubernetes ([6b073f3](https://github.com/rtrentin73/carlos-the-architect/commit/6b073f33329beb2c426602a584765bb163a1c55e))
* Auto-deploy Redis credentials to Kubernetes ([2b29325](https://github.com/rtrentin73/carlos-the-architect/commit/2b293250bc6e19067e12f1020cd46cfcbb16bf07))
* Change Carlos background to tiled pattern of small images ([78fb62f](https://github.com/rtrentin73/carlos-the-architect/commit/78fb62f195dc1a7c1a2108f27c159be4b9f01a79))
* Change Carlos background to tiled pattern of small images ([e1093df](https://github.com/rtrentin73/carlos-the-architect/commit/e1093dfcb89f0bf99716ea946f5da54cec7fcd44))
* Display total tokens and duration in design history ([b790af2](https://github.com/rtrentin73/carlos-the-architect/commit/b790af2876fd8cbdd20624b74d42d4f82dffd5dd))
* Display total tokens and duration in design history ([7f18127](https://github.com/rtrentin73/carlos-the-architect/commit/7f181272ebf2bc180ee7d4fab2268e35dd74a985))
* Enhance design prompts for production-ready architecture outputs ([d41da59](https://github.com/rtrentin73/carlos-the-architect/commit/d41da59fc7ee5d59efd3ba02881835696dcccf77))
* Enhance Mermaid diagram styling with professional theme ([22d8f53](https://github.com/rtrentin73/carlos-the-architect/commit/22d8f534dcd1d7b1642b08794591716536db4cbc))
* Make requirements gathering interactive with user answers ([e7ca224](https://github.com/rtrentin73/carlos-the-architect/commit/e7ca224907003c81cdb6d46704194bf71f6bd441))
* Migrate design cache to Azure Cache for Redis ([3fd1435](https://github.com/rtrentin73/carlos-the-architect/commit/3fd14355db7cc5bc848ba120354185c9f5090d9e))


### Bug Fixes

* Add aiohttp dependency for Cosmos DB async client ([b345dcb](https://github.com/rtrentin73/carlos-the-architect/commit/b345dcbded7374244b120927fdf4390cd7050bc3))
* Add aiohttp dependency for Cosmos DB async client ([855ae85](https://github.com/rtrentin73/carlos-the-architect/commit/855ae85992afc132973c09bb67ca570bff5a5ff3))
* Add api-version query parameter for Azure AI Foundry ([8141611](https://github.com/rtrentin73/carlos-the-architect/commit/81416114aac1d3267427d3c42e53ba62804c815c))
* Add cross-partition query support for Cosmos DB aggregates ([09cda8e](https://github.com/rtrentin73/carlos-the-architect/commit/09cda8e7359297bdbd973749147c249313a31a4f))
* Add cross-partition query support for Cosmos DB aggregates ([68164b2](https://github.com/rtrentin73/carlos-the-architect/commit/68164b2a7102332fb378abf1c1b01e87e040f28d))
* Add missing admin audit and user management endpoints ([b9c49ba](https://github.com/rtrentin73/carlos-the-architect/commit/b9c49ba2360356f65c4805ae61f8971a6320ca8d))
* Add missing admin audit and user management endpoints ([62e0a0b](https://github.com/rtrentin73/carlos-the-architect/commit/62e0a0be8f3ceed8da4d052b1e63a5f6dc88400e))
* Add namespace flag to kubectl commands in CI/CD ([dd9986d](https://github.com/rtrentin73/carlos-the-architect/commit/dd9986dc1ff940884147ffaf6b8e850962b3d6bf))
* Add pre-cleanup step to delete stale release-please branch ([42f3188](https://github.com/rtrentin73/carlos-the-architect/commit/42f31887ed287c7e273ebcdf267812dd9e1a3ef8))
* Add pre-cleanup step to delete stale release-please branch ([f42e344](https://github.com/rtrentin73/carlos-the-architect/commit/f42e34457c3f820c81b8f2be2ce99c994db33d17))
* Add python-multipart dependency for OAuth2 form data ([d48e2c3](https://github.com/rtrentin73/carlos-the-architect/commit/d48e2c31f1a8d3e59423358b84be5437cb0cca59))
* Add python-multipart dependency for OAuth2 form data ([051ba5b](https://github.com/rtrentin73/carlos-the-architect/commit/051ba5b6cc7b16c548a4e779a5018698f4c221bc))
* Align feedback dashboard analytics with backend response ([a1e4ae1](https://github.com/rtrentin73/carlos-the-architect/commit/a1e4ae13c90d28c17c9c177cf587e34f22c1ecd9))
* Align feedback dashboard analytics with backend response ([f2a45c9](https://github.com/rtrentin73/carlos-the-architect/commit/f2a45c9db7ffca354db824f0b653b64b514af79f))
* Base64 encode content for Azure Document Intelligence API ([bf676be](https://github.com/rtrentin73/carlos-the-architect/commit/bf676be603296058f21f1a65a659d3450680e793))
* Base64 encode content for Azure Document Intelligence API ([1aa3620](https://github.com/rtrentin73/carlos-the-architect/commit/1aa3620f47f4bdd3dc97057d2900528fa2872493))
* Configure forwarded-allow-ips for Kubernetes proxy headers ([011f496](https://github.com/rtrentin73/carlos-the-architect/commit/011f496496e469f484c6bb801538e3133270668d))
* Configure forwarded-allow-ips for Kubernetes proxy headers ([ae57e82](https://github.com/rtrentin73/carlos-the-architect/commit/ae57e8232e29bbe25423e89895da24090daed9a2))
* Correct feedback endpoint URL in FeedbackDashboard ([e5c3ff7](https://github.com/rtrentin73/carlos-the-architect/commit/e5c3ff7238872061b061bb2c553602299ce6b0a2))
* Correct Terraform argument to enable_auto_scaling for AKS cluster autoscaler ([79ec9ea](https://github.com/rtrentin73/carlos-the-architect/commit/79ec9ea0be6f40384e1c579877dca7a6888867fc))
* Enforce complete Terraform code output in corrector ([08f08a2](https://github.com/rtrentin73/carlos-the-architect/commit/08f08a22b026d4470408104ee640dfbb98095e7f))
* Fetch Azure secrets in deploy-backend job to fix masking issues ([5ce112e](https://github.com/rtrentin73/carlos-the-architect/commit/5ce112e783427a5a807ec45c277f4f1eced36696))
* Fetch Azure secrets in deploy-backend job to fix masking issues ([264924c](https://github.com/rtrentin73/carlos-the-architect/commit/264924ce870ec1876cb1d29f962641148a8247a6))
* Improve Terraform validation status parsing for feedback loop ([4e955b2](https://github.com/rtrentin73/carlos-the-architect/commit/4e955b2bba63cefe95384c11cdde740c46216d4a))
* Improve Terraform validation status parsing with better regex ([92ddbc6](https://github.com/rtrentin73/carlos-the-architect/commit/92ddbc69bad8dfb1667565a1a4859a6e967ef89c))
* Include api-version in base_url for Azure AI Foundry and GitHub Models to resolve missing query parameter error ([c69931f](https://github.com/rtrentin73/carlos-the-architect/commit/c69931f44752f0184c8cf725f39068766bbe397e))
* Override lodash-es to 4.17.23 to resolve CVE-2025-13465 ([e3f1129](https://github.com/rtrentin73/carlos-the-architect/commit/e3f1129753c6a696d7d6f3a4ed1a1ac533b3bec0))
* Pin bcrypt to &lt;5.0 to avoid passlib compatibility issue ([a525ab1](https://github.com/rtrentin73/carlos-the-architect/commit/a525ab1daa5e2e5d10d88a038b94fb1db3e00dde))
* Properly capture sensitive Terraform outputs in CI/CD workflow ([db22bcb](https://github.com/rtrentin73/carlos-the-architect/commit/db22bcbe0bacfe9ff0e390b13f139f1c099f4204))
* Remove api_version from ChatOpenAI to avoid unexpected keyword argument error ([0242e1d](https://github.com/rtrentin73/carlos-the-architect/commit/0242e1d7dd79ffe7342737c9c0abfb4ab99b83b2))
* Remove duplicate functions and fix require_admin definition order ([acba2bf](https://github.com/rtrentin73/carlos-the-architect/commit/acba2bfceb744c5f6f122a7d80db860682814d22))
* Remove duplicate functions and fix require_admin definition order ([4d6b07d](https://github.com/rtrentin73/carlos-the-architect/commit/4d6b07d0a958a16c7c0b92e3f73cfc660e445604))
* Remove duplicate redis-password in Kubernetes secrets ([c862f35](https://github.com/rtrentin73/carlos-the-architect/commit/c862f35272be1e90084c2b44b40a25fd0201c3e8))
* Remove unused dependencies causing Docker build failure ([34d682d](https://github.com/rtrentin73/carlos-the-architect/commit/34d682dea5c91db31db5b324122424062551bb2e))
* Remove unused dependencies causing Docker build failure ([0365c76](https://github.com/rtrentin73/carlos-the-architect/commit/0365c76ec6ba8b91a7b07f7edf00d10f107d088c))
* Reset all agent token counts when starting new design ([4b07a25](https://github.com/rtrentin73/carlos-the-architect/commit/4b07a256d422a32e84afe20732a23a5dc9bfe0da))
* Reset all agent token counts when starting new design ([1f0ab61](https://github.com/rtrentin73/carlos-the-architect/commit/1f0ab619d60a18ea5cc5a79fa1a357ece1d2204c))
* Simplify Azure AI Foundry endpoint handling ([e816596](https://github.com/rtrentin73/carlos-the-architect/commit/e81659681769a4948693d6a5770140f8dc4d7f28))
* Simplify Azure AI Foundry endpoint handling ([5a7d499](https://github.com/rtrentin73/carlos-the-architect/commit/5a7d499fdfe13827d933830a3b9ceeb2d5febbc8))
* Stream all agent tokens to AgentChatView in real-time ([784b30e](https://github.com/rtrentin73/carlos-the-architect/commit/784b30ef203bf2400a13d683ccc95dbd0b66cb83))
* Switch to uvicorn directly to fix proxy headers issue ([7ba117f](https://github.com/rtrentin73/carlos-the-architect/commit/7ba117f46ea45b5850d70aa57a4fd0e78333a46d))
* Switch to uvicorn directly to fix proxy headers issue ([5edf261](https://github.com/rtrentin73/carlos-the-architect/commit/5edf2613a87b4a990d034a7bd06eff04dc04fc78))
* Update agent transcript parser to match all agent headers ([4054b6a](https://github.com/rtrentin73/carlos-the-architect/commit/4054b6a80d60f366584c2a84fded7926a86db938))
* Update Azure OpenAI API version to 2024-08-01-preview ([67dae7f](https://github.com/rtrentin73/carlos-the-architect/commit/67dae7f75e721af019c03392033bd72ce932b8e8))
* Update Azure OpenAI API version to 2025-01-01-preview ([b8e4d81](https://github.com/rtrentin73/carlos-the-architect/commit/b8e4d8130e648ba66a83bdff57cafdbecaeabb5e))
* Update Azure OpenAI endpoint pattern to cognitiveservices.azure.com ([1a8139d](https://github.com/rtrentin73/carlos-the-architect/commit/1a8139d6768099a873e6797d4b2d649c42e77f74))
* Update release-please workflow and config ([34aced9](https://github.com/rtrentin73/carlos-the-architect/commit/34aced95c26d7b5501b518e510f500f886eda5c9))
* Update release-please workflow and config ([4bb84c7](https://github.com/rtrentin73/carlos-the-architect/commit/4bb84c7fa79ab950d6c93ca0ee298e0577ac4d02))
* Upgrade Node.js from 18 to 20 in frontend Dockerfile ([6bae3f3](https://github.com/rtrentin73/carlos-the-architect/commit/6bae3f3b327faaed33fd2aca965d9e8442fd7d2c))
* Use Azure CLI to fetch sensitive credentials directly ([fa56b31](https://github.com/rtrentin73/carlos-the-architect/commit/fa56b31750aae985883d8e3338044458c32a6edb))
* Use Azure CLI to fetch sensitive credentials directly ([8b3a384](https://github.com/rtrentin73/carlos-the-architect/commit/8b3a384b7af8b3d7b5a19cc8556e0882bbf8d86f))
* Use AzureChatOpenAI for Azure AI Foundry and GitHub Models to properly handle api-version and avoid 404 errors ([3a19805](https://github.com/rtrentin73/carlos-the-architect/commit/3a198053db41c7c29ffd3e422616dfd7890fe16d))
* Use correct API version for GitHub Models (2024-05-01-preview) to resolve 'API version not supported' error ([1af09dc](https://github.com/rtrentin73/carlos-the-architect/commit/1af09dce5aa88f2f96947b4bb6e03f182a1039bd))
* Use GitHub secrets for sensitive values with Azure CLI fallback ([f3fd292](https://github.com/rtrentin73/carlos-the-architect/commit/f3fd292ff2f00cd1433e1c75ffb31e872f176616))
* Use indices instead of objects in LLM pool tracking ([9720e5a](https://github.com/rtrentin73/carlos-the-architect/commit/9720e5ad1689c73651fa90f3a9621df4b3e843e0))
* Use JSON output to capture sensitive Terraform values ([dac3557](https://github.com/rtrentin73/carlos-the-architect/commit/dac35573507692b9472b5ecbb6e7a80b97ba0bba))
* Use JSON output to capture sensitive Terraform values ([324f86c](https://github.com/rtrentin73/carlos-the-architect/commit/324f86c577695e08699357a0046f69f4d942cbd2))
* Use stable Azure OpenAI API version 2024-02-01 ([0bff9fb](https://github.com/rtrentin73/carlos-the-architect/commit/0bff9fb1afe2c2897f21e0b192346ea2f7943133))


### Performance Improvements

* Add multi-model support for cost optimization ([43910f3](https://github.com/rtrentin73/carlos-the-architect/commit/43910f365d784fd9ee3f74f05e8a6b5ff2e557e5))
* Add multi-model support for cost optimization ([3f4b939](https://github.com/rtrentin73/carlos-the-architect/commit/3f4b939f8c2087241bdcd845c29d7ed67350ccca))
* Implement prompt caching with system/human messages ([7588e51](https://github.com/rtrentin73/carlos-the-architect/commit/7588e510ef5ea37aa8e16ce3ba7defa510b7fb3b))
* Implement prompt caching with system/human messages ([25b040f](https://github.com/rtrentin73/carlos-the-architect/commit/25b040f90469db11ce2f60ebd3de85466f47b4e3))
* Run Security, Cost, and Reliability analysts in parallel ([b0ce870](https://github.com/rtrentin73/carlos-the-architect/commit/b0ce8706c336a6537d0b0055eec646b2243bc9f6))
* Run Security, Cost, and Reliability analysts in parallel ([e302b09](https://github.com/rtrentin73/carlos-the-architect/commit/e302b09af3f2b4bc27b8f1b282b4e51c732276cd))


### Documentation

* Add Azure AI Document Intelligence to documentation ([e2cdf77](https://github.com/rtrentin73/carlos-the-architect/commit/e2cdf77ac64911be2dc7fb296ed4117b1bfa8c87))
* Add comprehensive agentic SDLC architecture documentation ([8e71215](https://github.com/rtrentin73/carlos-the-architect/commit/8e7121550de57e476bce08ee6ea35b30d429b04e))
* Add enterprise roadmap and tactical improvements ([f556116](https://github.com/rtrentin73/carlos-the-architect/commit/f5561161109618323af886dd24f26a0d35a13ce8))
* Add enterprise roadmap and tactical improvements ([abcd492](https://github.com/rtrentin73/carlos-the-architect/commit/abcd492cd034bfee592e810b0bb0857da499d664))
* Add OAuth authentication to roadmap strengths ([88e4730](https://github.com/rtrentin73/carlos-the-architect/commit/88e47304fd7364da7ee35447230c798add14f9b5))
* Add OAuth authentication to roadmap strengths ([391c665](https://github.com/rtrentin73/carlos-the-architect/commit/391c66589404e86023002c6c742833497e8d2b8b))
* Enhance API documentation with tags, summaries, and descriptions ([37f6c98](https://github.com/rtrentin73/carlos-the-architect/commit/37f6c980dcd5457283c0280e4d10906b5f887a7a))
* Enhance API documentation with tags, summaries, and descriptions ([2deedfb](https://github.com/rtrentin73/carlos-the-architect/commit/2deedfb17280f2cb9044825bd67ceab758174827))
* Reorganize documentation into docs/ folder ([6dabc1f](https://github.com/rtrentin73/carlos-the-architect/commit/6dabc1fc128eef475e1bc6fb10495837234be8a4))
* Update AGENTIC_SDLC.md with historical learning feature ([2e74cf5](https://github.com/rtrentin73/carlos-the-architect/commit/2e74cf50b865690331aef52ca4316a0fe6e8fed5))
* Update configuration for local dev vs GitHub Secrets ([71a9962](https://github.com/rtrentin73/carlos-the-architect/commit/71a9962f1cf5ab4dc4858190e42b9604d6d91a93))
* Update documentation for Redis caching and Cosmos DB feedback ([a0d282b](https://github.com/rtrentin73/carlos-the-architect/commit/a0d282be65079dc2ea8d232528c949813081f112))
* Update documentation for Redis caching and Cosmos DB feedback ([c0510a3](https://github.com/rtrentin73/carlos-the-architect/commit/c0510a3742c3495844ec622eeecb37c11080caa2))
* Update roadmap - mark audit logs as completed ([cf40d92](https://github.com/rtrentin73/carlos-the-architect/commit/cf40d92a5a7ccf7e151d10f364895f56ab068f8f))
* Update roadmap - mark audit logs as completed ([70fec48](https://github.com/rtrentin73/carlos-the-architect/commit/70fec4837ee63a3092531d700332a335e505f1a5))

## [0.2.0](https://github.com/rtrentin73/carlos-the-architect/compare/v0.1.0...v0.2.0) (2026-01-23)


### Features

* Add Azure deployment with Terraform and GitHub Actions ([0cc4ede](https://github.com/rtrentin73/carlos-the-architect/commit/0cc4edee983588271381c9d14ff265c4f53d36a8))
* add design recommender and architecture documentation ([afbdc0c](https://github.com/rtrentin73/carlos-the-architect/commit/afbdc0c00340b98808c54d6dea8ec01d45d59c8a))
* Add GitHub Variables for configurable deployment ([3fefe68](https://github.com/rtrentin73/carlos-the-architect/commit/3fefe68f27fc75e7aee1e68abeceda03f81f99eb))
* add Live Activity view to monitor agent streaming in real-time ([e19ad05](https://github.com/rtrentin73/carlos-the-architect/commit/e19ad05076d8e8dc66e226eb604b6bd3f025408f))
* Add Terraform Coder agent for IaC generation ([6590587](https://github.com/rtrentin73/carlos-the-architect/commit/6590587a90e400a05f180156bedfa22d098c279c))
* Add Terraform Validator agent for IaC code review ([783a7c7](https://github.com/rtrentin73/carlos-the-architect/commit/783a7c7efb9708264f16b592c49c953410ade30d))
* add Terraform Validator to Live Activity monitor ([2e8dda2](https://github.com/rtrentin73/carlos-the-architect/commit/2e8dda2889518dfd9ed4d4ac1c3dafbab5545023))
* display token consumption per design in Cloud History ([1664fc1](https://github.com/rtrentin73/carlos-the-architect/commit/1664fc107127fe7f1e09f2210939d23436569b54))
* enhance Live Activity view with detailed progress tracking ([510bc07](https://github.com/rtrentin73/carlos-the-architect/commit/510bc07743ba998f037f8bf72c23396117a3dd63))
* implement real-time agent streaming with SSE ([db21494](https://github.com/rtrentin73/carlos-the-architect/commit/db214940b9f2f36e40d7ab61ae85eb83acf035c7))


### Bug Fixes

* Switch to Free tier (F1) App Service with Python runtime ([73c34c2](https://github.com/rtrentin73/carlos-the-architect/commit/73c34c2ba993b4e550811755408454eb31559b4c))


### Performance Improvements

* run Carlos and Ronei agents in parallel for 2x faster execution ([4b9182d](https://github.com/rtrentin73/carlos-the-architect/commit/4b9182d569bb123d4970d7f217139074fc374373))

## [Unreleased]

### Added

### Changed

### Deprecated

### Removed

### Fixed

### Security
