from python_framework.api.src.service import WebBrowser
from python_helper import Constant as c
from python_helper import log, StringHelper, Function, ReflectionHelper, ObjectHelper, SettingHelper
from flask import Response, request
import flask_restful
from python_framework.api.src.enumeration.HttpStatus import HttpStatus
from python_framework.api.src.helper import Serializer
from python_framework.api.src.service import GlobalException
from python_framework.api.src.service import Security
from python_framework.api.src.service.openapi import OpenApiManager
import globals
import json

FRAMEWORK_GLOBALS_INSTANCE = None

KW_URL = 'url'
KW_DEFAULT_URL = 'defaultUrl'
KW_MODEL = 'model'
KW_API = 'api'
KW_APP = 'app'

KW_METHOD = 'method'

KW_RESOURCE = 'resource'

PYTHON_FRAMEWORK_MODULE_NAME = 'python_framework'
PYTHON_FRAMEWORK_INTERNAL_MODULE_NAME_LIST = [
    'python_framework',
    'TestApi',
    'DevTestApi',
    'LocalTestApi'
]
KW_CONTROLLER_RESOURCE = 'Controller'
KW_SCHEDULER_RESOURCE = 'Scheduler'
KW_SERVICE_RESOURCE = 'Service'
KW_CLIENT_RESOURCE = 'Client'
KW_REPOSITORY_RESOURCE = 'Repository'
KW_VALIDATOR_RESOURCE = 'Validator'
KW_MAPPER_RESOURCE = 'Mapper'
KW_HELPER_RESOURCE = 'Helper'
KW_CONVERTER_RESOURCE = 'Converter'
PYTHON_FRAMEWORK_RESOURCE_NAME_DICTIONARY = {
    KW_CONTROLLER_RESOURCE : [
        'ActuatorHealthController'
    ],
    KW_SCHEDULER_RESOURCE : [],
    KW_SERVICE_RESOURCE : [
        'ActuatorHealthService'
    ],
    KW_CLIENT_RESOURCE : [],
    KW_REPOSITORY_RESOURCE : [
        'ActuatorHealthRepository'
    ],
    KW_VALIDATOR_RESOURCE : [],
    KW_MAPPER_RESOURCE : [],
    KW_HELPER_RESOURCE : [],
    KW_CONVERTER_RESOURCE : [
        'ActuatorHealthConverter'
    ]
}
KW_RESOURCE_LIST = list(PYTHON_FRAMEWORK_RESOURCE_NAME_DICTIONARY.keys())

KW_PARAMETERS = 'params'
KW_HEADERS = 'headers'

def runGlobals(
    filePath
    , successStatus = False
    , settingStatus = False
    , debugStatus = False
    , warningStatus = False
    , wrapperStatus = False
    , failureStatus = False
    , errorStatus = False
    , testStatus = False
    , logStatus = False
) :
    return globals.newGlobalsInstance(
        filePath
        , successStatus = successStatus
        , settingStatus = settingStatus
        , debugStatus = debugStatus
        , warningStatus = warningStatus
        , wrapperStatus = wrapperStatus
        , failureStatus = failureStatus
        , errorStatus = errorStatus
        , testStatus = testStatus
        , logStatus = logStatus
    )

@Function
def initialize(
    apiInstance
    , defaultUrl = None
    , openInBrowser = False
    , filePath = None
    , successStatus = False
    , settingStatus = False
    , debugStatus = False
    , warningStatus = False
    , wrapperStatus = False
    , failureStatus = False
    , errorStatus = False
    , testStatus = False
    , logStatus = False
) :
    if ObjectHelper.isNone(apiInstance) :
        globalsInstance = runGlobals(
            filePath
            , successStatus = successStatus
            , settingStatus = settingStatus
            , debugStatus = debugStatus
            , warningStatus = warningStatus
            , wrapperStatus = wrapperStatus
            , failureStatus = failureStatus
            , errorStatus = errorStatus
            , testStatus = testStatus
            , logStatus = logStatus
        )
    defaultUrl
    openInBrowser
    url = getApiUrl(apiInstance)
    if defaultUrl :
        url = f'{url}{defaultUrl}'
    def inBetweenFunction(function,*argument,**keywordArgument) :
        log.debug(initialize,f'''{function.__name__} method''')
        if (openInBrowser) :
            log.debug(initialize,f'''Openning "{url}" url in rowser''')
            # WebBrowser.openUrlInChrome(url)
            WebBrowser.openUrl(url)
        def innerFunction(*args,**kwargs) :
            try :
                functionReturn = function(*args,**kwargs)
            except Exception as exception :
                raise Exception(f'Failed to initialize. Cause: {str(exception)}')
            return functionReturn
        return innerFunction
    return inBetweenFunction

def runApi(*args, api=None, **kwargs) :
    if ObjectHelper.isNone(api) :
        api = getApi()
    muteLogs(api.app)
    if 'host' not in kwargs and api.host :
        kwargs['host'] = api.host
    if 'port' not in kwargs and api.port :
        kwargs['port'] = api.port
    apiUrl = getApiUrl(api)
    log.success(runApi, f'Api will run at {apiUrl}')
    log.success(runApi, f'Documentation will be available at {apiUrl}/swagger')
    api.app.run(*args, **kwargs)

@Function
def getApiUrl(api) :
    apiUrl = None
    try :
        apiUrl = f'{api.scheme}://{api.host}{c.BLANK if ObjectHelper.isEmpty(api.port) else f"{c.COLON}{api.port}"}{api.baseUrl}'
    except Exception as exception :
        log.error(getApiUrl.__class__, 'Not possible to parse pai url', exception)
    return apiUrl

@Function
def muteLogs(app) :
    import logging
    from werkzeug.serving import WSGIRequestHandler
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.disabled = True
    app.logger.disabled = True
    WSGIRequestHandler.log = lambda self, type, message, *args: None ###- getattr(werkzeug_logger, type)('%s %s' % (self.address_string(), message % args))

@Function
def getRequestBodyAsJson(contentType, requestClass) :
    try :
        if OpenApiManager.DEFAULT_CONTENT_TYPE == contentType :
            requestBodyAsJson = request.get_json()
        elif OpenApiManager.MULTIPART_X_MIXED_REPLACE in contentType :
            requestBodyAsJson = request.get_data()
        else :
            raise Exception(f'Content type "{contentType}" not implemented')
    except Exception as exception :
        raise GlobalException.GlobalException(message='Not possible to parse the request', logMessage=str(exception), status=HttpStatus.BAD_REQUEST)
    validateBodyAsJson(requestBodyAsJson, requestClass)
    return requestBodyAsJson

@Function
def validateBodyAsJson(requestBodyAsJson, requestClass) :
    if ObjectHelper.isNotNone(requestClass) :
        requestBodyAsJsonIsList = ObjectHelper.isList(requestBodyAsJson)
        requestClassIsList = ObjectHelper.isList(requestClass) and ObjectHelper.isList(requestClass[0])
        if not ((requestBodyAsJsonIsList and requestClassIsList) or (not requestBodyAsJsonIsList and not requestClassIsList)) :
            raise GlobalException.GlobalException(message='Bad request', logMessage='Bad request', status=HttpStatus.BAD_REQUEST)

@Function
@Security.jwtRequired
def securedControllerMethod(
    args,
    kwargs,
    contentType,
    resourceInstance,
    resourceInstanceMethod,
    roleRequired,
    requestHeaderClass,
    requestParamClass,
    requestClass,
    logRequest
) :
    if not Security.getRole() in roleRequired :
        raise GlobalException.GlobalException(message='Role not allowed', logMessage=f'''Role {Security.getRole()} trying to access denied resourse''', status=HttpStatus.FORBIDEN)
    return publicControllerMethod(
        args,
        kwargs,
        contentType,
        resourceInstance,
        resourceInstanceMethod,
        requestHeaderClass,
        requestParamClass,
        requestClass,
        logRequest
    )

@Function
def publicControllerMethod(
    args,
    kwargs,
    contentType,
    resourceInstance,
    resourceInstanceMethod,
    requestHeaderClass,
    requestParamClass,
    requestClass,
    logRequest
) :
    if resourceInstanceMethod.__name__ in OpenApiManager.ABLE_TO_RECIEVE_BODY_LIST and requestClass :
        requestBodyAsJson = getRequestBodyAsJson(contentType, requestClass)
        if logRequest :
            log.prettyJson(
                resourceInstanceMethod,
                'bodyRequest',
                requestBodyAsJson,
                condition = logRequest,
                logLevel = log.DEBUG
            )
        if Serializer.requestBodyIsPresent(requestBodyAsJson) :
            serializerReturn = Serializer.convertFromJsonToObject(requestBodyAsJson, requestClass)
            args = getArgsWithSerializerReturnAppended(args, serializerReturn)
    addToKwargs(KW_HEADERS, requestHeaderClass, request.headers, kwargs)
    addToKwargs(KW_PARAMETERS, requestParamClass, request.args, kwargs)
    response = resourceInstanceMethod(resourceInstance,*args[1:],**kwargs)
    if response and Serializer.isSerializerCollection(response) and 2 == len(response) :
        return response
    raise GlobalException.GlobalException(logMessage=f'''Bad implementation of {resourceInstance.__class__.__name__}.{resourceInstanceMethod.__class__.__name__}() controller method''')

def addToKwargs(key, givenClass, valuesAsDictionary, kwargs) :
    if ObjectHelper.isNotEmpty(givenClass) :
        toClass = givenClass if ObjectHelper.isNotList(givenClass) else givenClass[0]
        kwargs[key] = Serializer.convertFromJsonToObject({k:v for k,v in valuesAsDictionary.items()}, toClass)

@Function
def jsonifyResponse(response, contentType, status) :
    return Response(Serializer.jsonifyIt(response),  mimetype=contentType, status=status)

@Function
def getArgsWithSerializerReturnAppended(args, argument) :
    args = [arg for arg in args]
    args.append(argument)
    # return [arg for arg in args]
    return args

@Function
def getArgumentInFrontOfArgs(args, argument) :
    return [argument, *args]

@Function
def getArgsWithResponseClassInstanceAppended(args, responseClass) :
    if responseClass :
        resourceInstance = args[0]
        objectRequest = args[1]
        serializerReturn = Serializer.convertFromObjectToObject(objectRequest, responseClass)
        args = getArgsWithSerializerReturnAppended(args, serializerReturn)
    return args

@Function
def getResourceFinalName(resourceInstance, resourceName=None) :
    if not resourceName :
        resourceName = resourceInstance.__class__.__name__
    for resourceType in KW_RESOURCE_LIST :
        if resourceName.endswith(resourceType) :
            resourceName = resourceName[:-len(resourceType)]
            break
    return f'{resourceName[0].lower()}{resourceName[1:]}'

@Function
def getResourceType(resourceInstance, resourceName = None) :
    if not resourceName :
        resourceName = resourceInstance.__class__.__name__
    for resourceType in KW_RESOURCE_LIST :
        if resourceName.endswith(resourceType):
            return resourceType

@Function
def setResource(apiInstance, resourceInstance, resourceName=None) :
    resourceName = getResourceFinalName(resourceInstance, resourceName=resourceName)
    ReflectionHelper.setAttributeOrMethod(apiInstance,resourceName,resourceInstance)

@Function
def bindResource(apiInstance,resourceInstance) :
    validateFlaskApi(apiInstance)
    validateResourceInstance(resourceInstance)
    setResource(ReflectionHelper.getAttributeOrMethod(apiInstance.resource, getResourceType(resourceInstance).lower()), resourceInstance)

@Function
def validateArgs(args, requestClass, method) :
    if ObjectHelper.isNotNone(requestClass) :
        resourceInstance = args[0]
        if Serializer.isSerializerList(requestClass) :
            if 0 < len(requestClass) :
                for index in range(len(requestClass)) :
                    if Serializer.isSerializerList(args[index + 1]) and len(args[index + 1]) > 0 :
                        expecteObjectClass = requestClass[index][0]
                        for objectInstance in args[index + 1] :
                            GlobalException.validateArgs(resourceInstance, method, objectInstance, expecteObjectClass)
                    else :
                        objectRequest = args[index + 1]
                        expecteObjectClass = requestClass[index]
                        GlobalException.validateArgs(resourceInstance, method, objectRequest, expecteObjectClass)
        else :
            objectRequest = args[1]
            expecteObjectClass = requestClass
            GlobalException.validateArgs(resourceInstance, method, objectRequest, expecteObjectClass)

def validateKwargs(kwargs, resourceInstance, innerResourceInstanceMethod, requestHeaderClass=None, requestParamClass=None) :
    classListToValidate = []
    instanceListToValidate = []
    if ObjectHelper.isNotEmpty(requestHeaderClass) :
        classListToValidate.append(requestHeaderClass if ObjectHelper.isNotList(requestHeaderClass) else requestHeaderClass[0])
        instanceListToValidate.append(kwargs.get(KW_HEADERS, {}))
    if ObjectHelper.isNotEmpty(requestParamClass) :
        classListToValidate.append(requestParamClass if ObjectHelper.isNotList(requestParamClass) else requestParamClass[0])
        instanceListToValidate.append(kwargs.get(KW_PARAMETERS, {}))
    validateArgs([resourceInstance, *instanceListToValidate], classListToValidate, innerResourceInstanceMethod)

@Function
def Controller(
    url = c.SLASH,
    tag = 'Tag not defined',
    description = 'Controller not descripted'
) :
    controllerUrl = url
    controllerTag = tag
    controllerDescription = description
    def Wrapper(OuterClass,*args,**kwargs):
        log.debug(Controller, f'''wrapping {OuterClass.__name__}''', None)
        class InnerClass(OuterClass, flask_restful.Resource):
            url = controllerUrl
            tag = controllerTag
            description = controllerDescription
            def __init__(self,*args,**kwargs):
                log.debug(OuterClass, f'in {InnerClass.__name__}.__init__(*{args},**{kwargs})', None)
                apiInstance = getApi()
                OuterClass.__init__(self)
                flask_restful.Resource.__init__(self,*args,**kwargs)
                self.service = apiInstance.resource.service
                self.globals = apiInstance.globals
        ReflectionHelper.overrideSignatures(InnerClass, OuterClass)
        return InnerClass
    return Wrapper

@Function
def ControllerMethod(
    url = c.SLASH,
    requestHeaderClass = None,
    requestParamClass = None,
    requestClass = None,
    responseClass = None,
    roleRequired = None,
    consumes = OpenApiManager.DEFAULT_CONTENT_TYPE,
    produces = OpenApiManager.DEFAULT_CONTENT_TYPE,
    logRequest = False,
    logResponse = False
):
    controllerMethodUrl = url
    controllerMethodRequestHeaderClass = requestHeaderClass
    controllerMethodRequestParamClass = requestParamClass
    controllerMethodRequestClass = requestClass
    controllerMethodResponseClass = responseClass
    controllerMethodRoleRequired = roleRequired
    controllerMethodProduces = produces
    controllerMethodConsumes = consumes
    controllerMethodLogRequest = logRequest
    controllerMethodLogResponse = logResponse
    def innerMethodWrapper(resourceInstanceMethod,*args,**kwargs) :
        log.debug(ControllerMethod, f'''wrapping {resourceInstanceMethod.__name__}''', None)
        def innerResourceInstanceMethod(*args,**kwargs) :
            # r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            # r.headers["Pragma"] = "no-cache"
            # r.headers["Expires"] = "0"
            # r.headers['Cache-Control'] = 'public, max-age=0'
            resourceInstance = args[0]
            completeResponse = None
            try :
                if ObjectHelper.isNotEmptyCollection(roleRequired) :
                    completeResponse = securedControllerMethod(
                        args,
                        kwargs,
                        consumes,
                        resourceInstance,
                        resourceInstanceMethod,
                        roleRequired,
                        requestHeaderClass,
                        requestParamClass,
                        requestClass,
                        logRequest
                    )
                else :
                    completeResponse = publicControllerMethod(
                        args,
                        kwargs,
                        consumes,
                        resourceInstance,
                        resourceInstanceMethod,
                        requestHeaderClass,
                        requestParamClass,
                        requestClass,
                        logRequest
                    )
                # print(f'completeResponse: {completeResponse}')
                validateResponseClass(responseClass, completeResponse)
            except Exception as exception :
                # print(exception)
                completeResponse = getCompleteResponseByException(exception, resourceInstance, resourceInstanceMethod)
                ###- request.method:              GET
                ###- request.url:                 http://127.0.0.1:5000/alert/dingding/test?x=y
                ###- request.base_url:            http://127.0.0.1:5000/alert/dingding/test
                ###- request.url_charset:         utf-8
                ###- request.url_root:            http://127.0.0.1:5000/
                ###- str(request.url_rule):       /alert/dingding/test
                ###- request.host_url:            http://127.0.0.1:5000/
                ###- request.host:                127.0.0.1:5000
                ###- request.script_root:
                ###- request.path:                /alert/dingding/test
                ###- request.full_path:           /alert/dingding/test?x=y
                ###- request.args:                ImmutableMultiDict([('x', 'y')])
                ###- request.args.get('x'):       y
            controllerResponse = completeResponse[0] if ObjectHelper.isNotNone(completeResponse[0]) else {'message' : completeResponse[1].enumName}
            status = completeResponse[1]
            if logResponse :
                log.prettyJson(
                    resourceInstanceMethod,
                    'bodyResponse',
                    json.loads(Serializer.jsonifyIt(controllerResponse)),
                    condition = logResponse,
                    logLevel = log.DEBUG
                )
            return jsonifyResponse(controllerResponse, produces, status)
        ReflectionHelper.overrideSignatures(innerResourceInstanceMethod, resourceInstanceMethod)
        innerResourceInstanceMethod.url = controllerMethodUrl
        innerResourceInstanceMethod.requestHeaderClass = controllerMethodRequestHeaderClass
        innerResourceInstanceMethod.requestParamClass = controllerMethodRequestParamClass
        innerResourceInstanceMethod.requestClass = controllerMethodRequestClass
        innerResourceInstanceMethod.responseClass = controllerMethodResponseClass
        innerResourceInstanceMethod.roleRequired = controllerMethodRoleRequired
        innerResourceInstanceMethod.produces = controllerMethodProduces
        innerResourceInstanceMethod.consumes = controllerMethodConsumes
        innerResourceInstanceMethod.logRequest = controllerMethodLogRequest
        innerResourceInstanceMethod.logResponse = controllerMethodLogResponse
        return innerResourceInstanceMethod
    return innerMethodWrapper

@Function
def SimpleClient() :
    def Wrapper(OuterClass, *args, **kwargs):
        log.debug(SimpleClient,f'''wrapping {OuterClass.__name__}''')
        class InnerClass(OuterClass):
            def __init__(self,*args,**kwargs):
                log.debug(OuterClass,f'in {InnerClass.__name__}.__init__(*{args},**{kwargs})')
                OuterClass.__init__(self,*args,**kwargs)
                self.globals = getApi().globals
        ReflectionHelper.overrideSignatures(InnerClass, OuterClass)
        return InnerClass
    return Wrapper

@Function
def SimpleClientMethod(requestClass=None):
    def innerMethodWrapper(resourceInstanceMethod,*args,**kwargs) :
        log.debug(SimpleClientMethod,f'''wrapping {resourceInstanceMethod.__name__}''')
        def innerResourceInstanceMethod(*args,**kwargs) :
            resourceInstance = args[0]
            try :
                validateArgs(args,requestClass,innerResourceInstanceMethod)
                methodReturn = resourceInstanceMethod(*args,**kwargs)
            except Exception as exception :
                raiseGlobalException(exception, resourceInstance, resourceInstanceMethod)
            return methodReturn
        ReflectionHelper.overrideSignatures(innerResourceInstanceMethod, resourceInstanceMethod)
        return innerResourceInstanceMethod
    return innerMethodWrapper

def getGlobalException(exception, resourceInstance, resourceInstanceMethod):
    apiInstance = getNullableApi()
    return GlobalException.handleLogErrorException(exception, resourceInstance, resourceInstanceMethod, apiInstance)

def raiseGlobalException(exception, resourceInstance, resourceInstanceMethod) :
    raise getGlobalException(exception, resourceInstance, resourceInstanceMethod)

def getCompleteResponseByException(exception, resourceInstance, resourceInstanceMethod) :
    exception = getGlobalException(exception, resourceInstance, resourceInstanceMethod)
    completeResponse = [{'message':exception.message, 'timestamp':str(exception.timeStamp)},exception.status]
    try :
        logErrorMessage = f'Error processing {resourceInstance.__class__.__name__}.{resourceInstanceMethod.__name__} request'
        if HttpStatus.INTERNAL_SERVER_ERROR <= exception.status :
            log.error(resourceInstance.__class__, logErrorMessage, exception)
        else :
            log.failure(resourceInstance.__class__, logErrorMessage, exception=exception)
    except Exception as logErrorMessageException :
        log.log(getCompleteResponseByException, 'Error logging exception at controller', exception=logErrorMessageException)
        log.error(log.error, 'Error processing request', exception)
    return completeResponse

def validateResponseClass(responseClass, controllerResponse) :
    if isNotPythonFrameworkHttpsResponse(controllerResponse) :
        raiseBadResponseImplementation(f'Python Framework response cannot be null. It should be a list like this: [{"RESPONSE_CLASS" if ObjectHelper.isNone(responseClass) else responseClass if ObjectHelper.isNotList(responseClass) else responseClass[0]}, HTTPS_CODE]')
    if ObjectHelper.isNotNone(responseClass) :
        if Serializer.isSerializerList(responseClass) :
            if 0 == len(responseClass) :
                log.warning(validateResponseClass,f'"responseClass" was not defined')
            elif 1 == len(responseClass) :
                if ObjectHelper.isNotList(responseClass[0])  :
                    if not isinstance(controllerResponse[0], responseClass[0]) :
                        raiseBadResponseImplementation(f'Response class does not match expected class. Expected "{responseClass[0].__name__}", response "{controllerResponse[0].__class__.__name__}"')
                elif ObjectHelper.isNotList(responseClass[0][0]) :
                    if ObjectHelper.isNotList(controllerResponse[0]) :
                        raiseBadResponseImplementation(f'Response is not a list. Expected "{responseClass[0].__class__.__name__}", but found "{controllerResponse[0].__class__.__name__}"')
                    elif Serializer.isSerializerList(controllerResponse[0]) and 0 < len(controllerResponse[0]) and not isinstance(controllerResponse[0][0], responseClass[0][0]) :
                        raiseBadResponseImplementation(f'Response element class does not match expected element class. Expected "{responseClass[0][0].__name__}", response "{controllerResponse[0][0].__class__.__name__}"')
        else :
            if not isinstance(controllerResponse[0], responseClass) :
                raiseBadResponseImplementation(f'Response class does not match expected class. Expected "{responseClass.__name__}", response "{controllerResponse[0].__class__.__name__}"')
    else :
        log.warning(validateResponseClass,f'"responseClass" was not defined')

def getClassName(instance) :
    return instance.__class__.__name__

def getModuleName(instance) :
    return instance.__class__.__module__

def getQualitativeName(instance) :
    return instance.__class__.__qualname__

def isPythonFrameworkHttpsResponse(controllerResponse) :
    return (ObjectHelper.isTuple(controllerResponse) or ObjectHelper.isList(controllerResponse)) and 2 == len(controllerResponse)

def isNotPythonFrameworkHttpsResponse(controllerResponse) :
    return not isPythonFrameworkHttpsResponse(controllerResponse)

def raiseBadResponseImplementation(cause):
    raise Exception(f'Bad response implementation. {cause}')

@Function
def getGlobals() :
    return globals.getGlobalsInstance()

def getApi() :
    api = None
    try:
        api = getGlobals().api
    except Exception as exception :
        raise Exception(f'Failed to return api from "globals" instance. Cause: {str(exception)}')
    return api

def getNullableApi() :
    api = None
    try :
        api = getApi()
    except Exception as exception :
        log.warning(getNullableApi, 'Not possible to get api', exception=exception)
    return api

def validateFlaskApi(instance) :
    apiClassName = flask_restful.Api.__name__
    moduleName = flask_restful.__name__
    if not apiClassName == getClassName(instance) and apiClassName == getQualitativeName(instance) and moduleName == getModuleName(instance) :
        raise Exception(f'Invalid "flask_restful.Api" instance. {apiInstance} is not an Api instance')

def validateResourceInstance(resourceInstance) :
    if ObjectHelper.isNone(resourceInstance) :
        raise Exception(f'Resource cannot be None')
