function openTaskDriver()
{
    window.open("chrome://collageclient/content/driver.xul", "Collage Task Driver", "chrome=false,width=600,height=400");
}

function ajaxTest()
{
    hostDef = {
        "serviceType": "JSON-RPC", 
        //"serviceURL": "http://127.0.0.1/~sburnett/cgi-bin/json.py",
        "serviceURL": "http://127.0.0.1:8000/cgi-bin/json.py",
        "sync": true,
        "methods":[ 
        {
            "name": "add", 
            "parameters":[
            {"name": "x"},
            {"name": "y"}  
            ]
        },
        {
            "name": "subtract", 
            "parameters":[
            {"name": "x"},
            {"name": "y"}  
            ]
        }
        ]
    }

    host = new dojo.rpc.JsonService({smdObj:hostDef});

    function doCalculate() {
        var x, y, ret;

        // fetch x and y from fields on page
        x = 2
        y = 3

        // invoke the method synchronously, get result
        // (you could do it asynchronously, by passing a third argument,
        // a function which takes a single argument - result object)

        //var myDeferred = host.add(x,y).addCallback(onCalculateDone);
        var myDeferred = host.callRemote("pow", [x,y]);
        myDeferred.addCallback(onCalculateDone);
        myDeferred.addErrback(onCalculateError);
    }

    function onCalculateDone(result) {
        alert(dojo.json.serialize(result));
    }

    function onCalculateError(err) {
        alert("ERROR: " + err.message);
    }

    doCalculate();
}
