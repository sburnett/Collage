<html>
    <head>
        <meta charset="UTF-8"/>
        <title>Collage Photo Donation</title>
        <link rel="stylesheet" type="text/css" href="http://yui.yahooapis.com/2.8.0r4/build/fonts/fonts-min.css" />
        <link rel="stylesheet" type="text/css" href="/static/button.css" />
        <link rel="stylesheet" type="text/css" href="/static/default.css" />
        <link rel="stylesheet" type="text/css" href="/static/fileuploader.css" />
        <script type="text/javascript" src="http://yui.yahooapis.com/2.8.0r4/build/yahoo-dom-event/yahoo-dom-event.js"></script>
        <script type="text/javascript" src="http://yui.yahooapis.com/2.8.0r4/build/element/element-min.js"></script>
        <script type="text/javascript" src="http://yui.yahooapis.com/2.8.0r4/build/button/button-min.js"></script>

        <script type="text/javascript" src="/static/utils.js"></script>
        <script type="text/javascript" src="/static/fileuploader.js"></script>
        <script type="text/javascript">
            window.onload = function() {
                var uploader = new qq.FileUploader({
                    element: document.getElementById('uploadButtonPlaceHolder'),
                    action: '/upload_file',
                    allowedExtensions: ['jpg', 'jpeg'],
                    sizeLimit: 10485760,
                    debug: false,
                    onComplete: function(id, fileName, responseJSON) {
                        if(responseJSON.success) {
                            filename = responseJSON.filename;
                            addImage("/thumbnail?filename=" + escape(filename), filename, true);

                            el = document.getElementById("vector_ids");
                            if (el.value === "") {
                                el.value = filename;
                            } else {
                                el.value += ";" + filename;
                            }
                        }
                    },
                    showMessage: function(message) { },
                    template: '<div class="qq-uploader">' +
                              '<div class="qq-upload-drop-area"><span>Drop photos here to upload</span></div>' +
                              '<div class="qq-upload-button">Click here to select photos</div>' +
                              '<ul class="qq-upload-list"></ul>' +
                              '</div>',
                    messages: {
                        typeError: "{file} has invalid extension. Only JPEG photos are allowed.",
                        sizeError: "{file} is too large, maximum photo size is {sizeLimit}.",
                        minSizeError: "{file} is too small, minimum photo size is {minSizeLimit}.",
                        emptyError: "{file} is empty, please select photos again without it.",
                        onLeave: "The photos are being uploaded, if you leave now the upload will be cancelled."
                    }
                });

                val = document.getElementById("vector_ids").value;
                if(val.length > 0) {
                    filenames = val.split(";");
                    for(var i = 0; i < filenames.length; i++) {
                        url = "/thumbnail?filename=" + escape(filenames[i]);
                        addImage(url, filenames[i], false);
                    }
                }
            };
        </script>

        <style>
            #tagsbox {
                width: 100%;
                border: 1px solid black;
                padding: 5px;
                margin-top: 5px;
                margin-bottom: 5px;
            }
            span.error {
                font-size: 1.3em;
                font-weight: bold;
                color: red;
                background-color: #ffdddd;
                border: 1px solid gray;
                padding: 4px;
                padding-left: 20px;
                padding-right: 20px;
            }
            input {
                font-size: 1.3em;
                font-weight: bold;
            }
            a.thumbCancel {
                font-size: 0;
                display: block;
                height: 14px;
                width: 14px;
                background-image: url(/static/images/cancelbutton.gif);
                background-repeat: no-repeat;
                background-position: -14px 0px;
                position: absolute;
                left: 0px;
                top: 0px;
            }
            a.thumbCancel:hover {
                background-position: 0px 0px;
            }
        </style>
    </head>

    <body class="yui-skin-sam">
        <h1>Collage Photo Donation</h1>
        <form id="form1" action="/upload" method="POST" enctype="multipart/form-data">
            {% if error %}
                <span class="error">{{error}}</span>
            {% endif %}
            <p><b>Step 1:</b> What photos would you like to donate? <small>(<a href="/static/faq.html#uploads" target="_blank">what's this?</a>)</small></p>
            <input type="hidden" name="vector_ids" id="vector_ids" value="{% if vector_ids %}{{vector_ids}}{% endif %}"/>
            <div id="uploadButtonPlaceHolder">
                <noscript><p>Please enable JavaScript to upload photos.</p></noscript>
            </div>
            <div id="thumbnails" style="margin-bottom: 20px">
            </div>

            <p><b>Step 2:</b> What is a title for these photos? <input class="box" type="text" name="title" size="50" value="{{title|default:""}}"/></p>
            <p><b>Step 3:</b> How many hours may we hold your photos before uploading them to Flickr? <input class="box" type="text" name="expiration" size="1" value="{{expiration|default:"24"}}"/> hours. <small>(<a href="/static/faq.html#expiration" target="_blank">what's this?</a>)</small></br></p>
            <p><b>Step 4:</b> What tags best describe your photos? Click <i>at least three</i> tags on this list: <small>(<a href="/static/faq.html#tags" target="_blank">what's this?</a>)</small>
            <script type="text/javascript">
            {% include "tags.tpl" %}
            </script>
            <div id="tagsbox">
            </div>
            <p><b>Step 5:</b> Donate your photos by clicking the button below.</p>
            <input type="submit" name="submit" value="Donate photos"/>
        </form>

        <a href="/logout">Logout</a>
    </body>
</html>
