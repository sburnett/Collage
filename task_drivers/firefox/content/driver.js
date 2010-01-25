function sleep(delay) {
    netscape.security.PrivilegeManager.enablePrivilege("UniversalXPConnect");
 
    var thread = Components.classes["@mozilla.org/thread-manager;1"].getService(Components.interfaces.nsIThreadManager).currentThread;
 
    this.delayed = true;
    setTimeout("this.delayed = false;", delay);
 
    while (this.delayed) {
        thread.processNextEvent(true);
    }
}

function print(msg) {
    window.dump(msg);
}

function println(msg) {
    window.dump(msg + "\n");
}

var DriverUtils = new function() {
    this.browserCheckInterval = 50;

    this.waitToLoad = function() {
        while(!this.contentLoaded) {
            sleep(this.browserCheckInterval);
        }
    };

    this.onFrameLoad = function() {
        this.contentLoaded = true;
    };

    this.getElementById = function(id) {
        return this.browser.contentDocument.getElementById(id);
    };

    this.loadUrl = function(url) {
        this.contentLoaded = false;
        this.browser.loadURI(url, this.browser.LOAD_FLAGS_NONE);
        this.waitToLoad();
    };

    this.setElementAttribute = function(id, key, value) {
        el = this.browser.contentDocument.getElementById(id);
        el.setAttribute(key, value);
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
        var clicker = document.createEvent("MouseEvents");
        clicker.initMouseEvent("click", true, true, window, 0,
                               0, 0, 0, 0,
                               false, false, false, false, 0, null);
        el.dispatchEvent(clicker);
    };

    this.clickElementId = function(id) {
        el = this.browser.contentDocument.getElementById(id);
        if(el === null) {
            throw new Error("Invalid element id " + id);
        }

        this.clickElement(el);
    };

    this.typeElement = function(el, ch) {
        var typer = document.createEvent("KeyboardEvent");
        typer.initKeyEvent("keypress", true, false, window,
                           false, false, false, false, 0, ch);
        el.dispatchEvent(typer);
    };

    this.typeElementId = function(id, ch) {
        el = this.browser.contentDocument.getElementById(id);
        if(el === null) {
            throw new Error("Invalid element id " + id);
        }

        this.typeElement(el, ch);
    };

    this.closeWindow = function() {
        window.close();
    }
};

hostDef = {
    "serviceType": "JSON-RPC", 
    "serviceURL": "http://127.0.0.1:8000",
    "sync": true,
    "methods":[ 
    {
        "name": "fetch_snippet", 
        "parameters":[]
    },
    {
        "name": "snippet_return", 
        "parameters":[
            {"name": "result"},
            {"name": "is_error"}
        ]
    }
    ]
};

function RpcError(message) {
    this.name = "RpcError";
    this.message = message || "";
}
RpcError.prototype = Error.prototype;

var SyncRpc = new function() {
    this.rpcHost = new dojo.rpc.JsonService({smdObj:hostDef});

    this.run = function(method, params) {
        this.callbackReceived = false;

        var myDeferred = this.rpcHost.callRemote(method, params);
        myDeferred.addCallback(function(r) { SyncRpc.onDone(r) });
        myDeferred.addErrback(function(e) { SyncRpc.onError(e) });

        this.resultReceived = false;
        this.errorReceived = false;
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

var TaskDriver = new function() {
    this.refreshInterval = 50;

    this.eventLoop = function() {
        while(true) {
            print("Fetching snippets...");
            snippet = this.fetchSnippet();
            println("done");

            if(snippet !== null) {
                try {
                    print("Executing snippet...");
                    result = this.executeSnippet(snippet);
                    println("done");

                    print("Returning snippet...");
                    this.snippetReturn(result, false);
                    println("done");
                } catch(error) {
                    println("Execution error: \"" + error.message + "\" at " + error.fileName + ":" + error.lineNumber);
                    this.snippetReturn(error.message, true);
                }
            }

            print("Sleeping...");
            sleep(this.refreshInterval);
            println("done");
        }
    };

    this.fetchSnippet = function() {
        try {
            return SyncRpc.run("fetch_snippet", []);
        } catch(error if error.name == "RpcError") {
            return null;
        }
    };

    this.snippetReturn = function(result, isError) {
        try {
            SyncRpc.run("snippet_return", [result, isError]);
        } catch(error if error.name == "RpcError") {
            println("Snippet return error: " + error.message);
        }
    };

    this.executeSnippet = function(snippet) {
        result = evalSnippet(snippet);
        println("Done executing snippet");
        if(result == undefined) {
            result = null;
        }
        return result;
    };
};

function evalSnippet(snippet) {
    println("About to execute snippet:");
    println(snippet);
    retval = eval(snippet);
    println("Got result: " + retval);
    return retval;
}

function WebProgressListener() {
    //this.url_ = url;
    this.QueryInterface = function (iid) {
        if (iid.equals(Components.interfaces.nsIWebProgressListener)
                || iid.equals(Components.interfaces.nsISupportsWeakReference)
                || iid.equals(Components.interfaces.nsISupports))
            return this;

        throw Components.results.NS_ERROR_NO_INTERFACE; 
    }

    this.onStateChange = function (webProgress, request, stateFlags, status) {
        var WPL = Components.interfaces.nsIWebProgressListener;
        println('onStateChange : [' + request.name + '], flags [' + stateFlags + ']');
        if(stateFlags & WPL.STATE_IS_NETWORK)
            println('STATE_IS_NETWORK');
        if((stateFlags & WPL.STATE_STOP)
                && (stateFlags & WPL.STATE_IS_WINDOW)
                && (stateFlags & WPL.STATE_IS_NETWORK)) {
            println('Done loading');
            DriverUtils.onFrameLoad();
        }
    }

    this.onLocationChange = function (webProgress, request, location) {
        println('onLocationChange : [' + request.name + ']');
    }

    this.onProgressChange = function (webProgress, request, curSelf, maxSelf, curTotal, maxTotal) {
        println('onProgressChange : [' + request.name + ']');
    }

    this.onStatusChange = function (webProgress, request, status, message) {
        println('onStatusChange : [' + request.name + ']');
    }

    this.onSecurityChange = function (webProgress, request, state) {
        println('onSecurityChange : [' + request.name + ']'); 
    } 
}

function onWindowLoad() {
    DriverUtils.browser = document.getElementById("drivenBrowser");
    DriverUtils.browser.addProgressListener(new WebProgressListener());
    DriverUtils.document = DriverUtils.browser.contentDocument;
    TaskDriver.eventLoop();
}

function onWindowClose() {
    clearTimeout(TaskDriver.refreshTimeId);
}
