include compose/.env

help:
	@echo "*********************************************"
	@echo
	@echo NGUML_ALLEN_IMAGE=${NGUML_ALLEN_IMAGE}
	@echo NGUML_DOWNLOAD_MODELS_STARTUP=${NGUML_DOWNLOAD_MODELS_STARTUP}
	@echo
	@echo "*********************************************"

local-nocache:
	docker build --no-cache ./docker/allen/ \
		-t ${NGUML_ALLEN_IMAGE}

local:
	docker build ./docker/allen/ \
		-t ${NGUML_ALLEN_IMAGE}
