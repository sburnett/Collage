function sleep(delay) {
    netscape.security.PrivilegeManager.enablePrivilege("UniversalXPConnect");
 
    var thread = Components.classes["@mozilla.org/thread-manager;1"].getService(Components.interfaces.nsIThreadManager).currentThread;
 
    this.delayed = true;
    setTimeout("this.delayed = false;", delay);
 
    while (this.delayed) {
        thread.processNextEvent(true);
    }
}

DriverUtils = new function DriverUtils() {
    this.browser = document.getElementById("drivenBrowser");
    this.browserCheckInterval = 50;

    this.waitToLoad = function() {
        while(!this.contentLoaded) {
            sleep(this.browserCheckInterval);
        }
    };

    this.onFrameLoad = function() {
        this.contentLoaded = true;
    };

    this.loadUrl = function(url) {
        if(this.contentPending) {
            throw "Content pending";
        } else {
            this.contentPending = true;
            this.contentLoaded = false;
            this.browser.setAttribute("src", url);
            this.waitToLoad();
        }
    };

    this.getUrlFromCache = function(url) {
        var ioserv = Components.classes["@mozilla.org/network/io-service;1"].getService(Components.interfaces.nsIIOService);
        var channel = ioserv.newChannel(url, 0, null);
        channel.loadFlags |= Components.interfaces.nsICachingChannel.LOAD_ONLY_FROM_CACHE;
        var stream = channel.open();

        if (channel instanceof Components.interfaces.nsIHttpChannel && channel.responseStatus != 200) {
            return "";
        }

        var bstream = Components.classes["@mozilla.org/binaryinputstream;1"].createInstance(Components.interfaces.nsIBinaryInputStream);
        bstream.setInputStream(stream);

        var size = 0;
        var file_data = "";
        while((size = bstream.available())) {
            file_data += bstream.readBytes(size);
        }

        return file_data;
    };

    this.clickElement = function(el) {
        if(this.contentPending) {
            throw "Content pending";
        }

        this.contentPending = true;
        this.contentLoaded = false;

        var clicker = document.createEvent("MouseEvents");
        clicker.initMouseEvent("click", true, true, window, 0,
                               0, 0, 0, 0,
                               false, false, false, false, 0, null);
        el.dispatchEvent(clicker);

        this.waitToLoad();
    };

    this.clickElementId = function(id) {
        el = this.browser.contentDocument.getElementById(id);
        if(el === null) {
            throw "Invalid element id " + id;
        }

        this.clickElement(id);
    };
};

hostDef = {
    "serviceType": "JSON-RPC", 
    "serviceURL": "http://127.0.0.1:8000",
    "sync": true,
    "methods":[ 
    {
        "name": "fetchSnippet", 
        "parameters":[]
    },
    {
        "name": "snippetReturn", 
        "parameters":[
            {"name": "snippetId"},
            {"name": "result"},
            {"name": "isError"}
        ]
    }
    ]
};

function RpcError(message) {
    this.name = "RpcError";
    this.message = message || "";
}
RpcError.prototype = Error.prototype;

SyncRpc = new function SynRpc() {
    this.rpcHost = new dojo.rpc.JsonService({smdObj:hostDef});

    this.run = function(method, params) {
        this.callbackReceived = false;

        var myDeferred = this.rpcHost.callRemote(method, params);
        myDeferred.addCallback(this.onDone);
        myDeferred.addErrback(this.onError);

        while(!this.resultReceived && !this.errorReceived) {
            sleep(50);
        }

        if(this.resultReceived) {
            return this.result;
        } else {
            throw new RpcError(this.error);
        }
    };

    this.onDone = function(result) {
        this.resultReceived = true;
        this.result = result;
    };

    this.onError = function(error) {
        this.errorReceived = true;
        this.error = error.message;
    };
};

TaskDriver = new function TaskDriver() {
    this.refreshInterval = 50;

    this.refresh = function() {
        snippetOb = this.fetchSnippet();

        if(snippetOb !== null) {
            try {
                result = this.executeSnippet(snippetOb.snippet);
            } catch(error) {
                this.snippetReturn(snippetOb.id, result);
            }
        }

        this.refreshTimeId = setTimeout(this.refresh, this.refreshInterval);
    };

    this.fetchSnippet = function() {
        try {
            result = SyncRpc.run("fetchSnippet", []);
            return dojo.json.serialize(result);
        } catch(error if error.name == "RpcError") {
            alert("Fetch snippet error: " + error.message);
            return null;
        }
    };

    this.snippetReturn = function(id, result, isError) {
        try {
            SyncRpc.run("snippetReturn", [id, result, isError]);
        } catch(error if error.name == "RpcError") {
            alert("Snippet return error: " + error.message);
        }
    };

    this.executeSnippet = function(snippet) {
        try {
            return evalSnippet(snippet);
        } catch(error) {
            return error;
        }
    };
};

function evalSnippet(snippet) {
    return eval(snippet);
}

function onWindowLoad() {
    TaskDriver.refresh();
}

function onWindowClose() {
    clearTimeout(TaskDriver.refreshTimeId);
}
