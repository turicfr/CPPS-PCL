import sys
import os
from urllib import pathname2url
from urlparse import urljoin
from cefpython3 import cefpython as cef

_tokens = []

class ClientHandler:
	def __init__(self, old_url, new_url):
		self.old_url = old_url
		self.new_url = new_url

	def GetResourceHandler(self, browser, frame, request):
		if request.GetUrl() != self.old_url:
			return None
		resHandler = ResourceHandler()
		resHandler._clientHandler = self
		resHandler._browser = browser
		resHandler._frame = frame
		resHandler._request = request
		self._AddStrongReference(resHandler)
		return resHandler

	_resourceHandlers = {}
	_resourceHandlerMaxId = 0

	def _AddStrongReference(self, resHandler):
		self._resourceHandlerMaxId += 1
		resHandler._resourceHandlerId = self._resourceHandlerMaxId
		self._resourceHandlers[resHandler._resourceHandlerId] = resHandler

	def _ReleaseStrongReference(self, resHandler):
		assert resHandler._resourceHandlerId in self._resourceHandlers, "resource handler not found, id = %s" % (resHandler._resourceHandlerId)
		del self._resourceHandlers[resHandler._resourceHandlerId]

class ResourceHandler:
	_resourceHandlerId = None
	_clientHandler = None
	_browser = None
	_frame = None
	_request = None
	_responseHeadersReadyCallback = None
	_webRequest = None
	_webRequestClient = None
	_offsetRead = 0

	def ProcessRequest(self, request, callback):
		self._responseHeadersReadyCallback = callback
		self._webRequestClient = WebRequestClient()
		self._webRequestClient._resourceHandler = self
		request.SetFlags(cef.Request.Flags["AllowCachedCredentials"] | cef.Request.Flags["AllowCookies"])
		request.SetUrl(self._clientHandler.new_url)
		self._webRequest = cef.WebRequest.Create(request, self._webRequestClient)
		return True

	def GetResponseHeaders(self, response, response_length_out, redirect_url_out):
		assert self._webRequestClient._response, "Response object empty"
		wrcResponse = self._webRequestClient._response
		response.SetStatus(wrcResponse.GetStatus())
		response.SetStatusText(wrcResponse.GetStatusText())
		response.SetMimeType(wrcResponse.GetMimeType())
		if wrcResponse.GetHeaderMultimap():
			response.SetHeaderMultimap(wrcResponse.GetHeaderMultimap())
		response_length_out[0] = self._webRequestClient._dataLength

	def ReadResponse(self, bytes_to_read, bytes_read_out, data_out, callback):
		if self._offsetRead < self._webRequestClient._dataLength:
			dataChunk = self._webRequestClient._data[self._offsetRead:self._offsetRead + bytes_to_read]
			self._offsetRead += len(dataChunk)
			data_out[0] = dataChunk
			bytes_read_out[0] = len(dataChunk)
			return True
		self._clientHandler._ReleaseStrongReference(self)
		return False

	def CanGetCookie(self, cookie):
		return True

	def CanSetCookie(self, cookie):
		return True

	def Cancel(self):
		pass

class WebRequestClient:
	_resourceHandler = None
	_data = ""
	_dataLength = -1
	_response = None

	def OnUploadProgress(self, web_request, current, total):
		pass

	def OnDownloadProgress(self, web_request, current, total):
		pass

	def OnDownloadData(self, web_request, data):
		self._data += data

	def OnRequestComplete(self, web_request):
		statusText = cef.WebRequest.Status.get(web_request.GetRequestStatus(), "Unknown")
		self._response = web_request.GetResponse()
		self._dataLength = len(self._data)
		self._resourceHandler._responseHeadersReadyCallback.Continue()

class External(object):
	def __init__(self):
		self._token = None

	def setToken(self, token):
		if self._token is not None:
			return
		self._token = token
		cef.QuitMessageLoop()

	def getToken(self):
		return self._token

def filename2url(filename):
	return urljoin("file:", pathname2url(os.path.abspath(filename)))

def get_tokens(count, retry=False):
	url = "https://play.cprewritten.net/"
	sys.excepthook = cef.ExceptHook
	settings = {
		"context_menu": {"enabled": False},
		"debug": False,
		"log_severity": cef.LOGSEVERITY_DISABLE
	}
	try:
		cef.Initialize(settings=settings)
		while count:
			browser = cef.CreateBrowserSync(window_title="reCAPTCHA")
			browser.SetBounds(0, 0, 314, 501)

			clientHandler = ClientHandler(url, filename2url("recaptcha.html"))
			browser.SetClientHandler(clientHandler)

			frame = browser.GetMainFrame()
			# frame.LoadString(html, url)
			frame.LoadUrl(url)

			external = External()
			bindings = cef.JavascriptBindings(bindToFrames=False, bindToPopups=False)
			bindings.SetObject("external", external)
			browser.SetJavascriptBindings(bindings)

			cef.MessageLoop()
			token = external.getToken()
			if retry and token is None:
				continue
			yield token
			count -= 1
		cef.Shutdown()
	finally:
		sys.excepthook = sys.__excepthook__

def get_token():
	if _tokens:
		return _tokens.pop()
	return list(get_tokens(1))[0]

def preload_tokens(count):
	_tokens.extend(get_tokens(count, True))
