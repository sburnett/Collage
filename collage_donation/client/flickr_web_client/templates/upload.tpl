<html>
    <head>
        <meta charset="UTF-8"/>
        <title>Collage Photo Donation</title>
        <link rel="stylesheet" type="text/css" href="http://yui.yahooapis.com/2.8.0r4/build/fonts/fonts-min.css" />
        <link rel="stylesheet" type="text/css" href="/static/button.css" />
        <link rel="stylesheet" type="text/css" href="/static/default.css" />
        <script type="text/javascript" src="http://yui.yahooapis.com/2.8.0r4/build/yahoo-dom-event/yahoo-dom-event.js"></script>
        
        <script type="text/javascript" src="http://yui.yahooapis.com/2.8.0r4/build/element/element-min.js"></script>
        <script type="text/javascript" src="http://yui.yahooapis.com/2.8.0r4/build/button/button-min.js"></script>

        <script type="text/javascript" src="/static/swfupload/swfupload.js"></script>
        <script type="text/javascript" src="/static/swfupload.queue.js"></script>
        <script type="text/javascript" src="/static/fileprogress.js"></script>
        <script type="text/javascript" src="/static/handlers.js"></script>
        <script type="text/javascript">
            var swfu;

            window.onload = function() {
                var settings = {
                    flash_url : "/static/swfupload/swfupload.swf",
                    upload_url: "/upload_file",
                    file_post_name: "vector",
                    post_params: {"token" : "{{token}}", "userid" : "{{userid}}"},
                    file_size_limit : "10 MB",
                    file_types : "*.jpeg;*.jpg",
                    file_types_description : "All Files",
                    file_upload_limit : 100,
                    file_queue_limit : 0,
                    custom_settings : {
                        progressTarget : "fsUploadProgress",
                        cancelButtonId : "btnCancel"
                    },
                    debug: false,

                    // Button settings
                    button_image_url: "/static/images/TestImageNoText_65x29.png",
                    button_width: "65",
                    button_height: "29",
                    button_placeholder_id: "spanButtonPlaceHolder",
                    button_text: '<span class="theFont">Upload</span>',
                    button_text_style: ".theFont { font-size: 16; }",
                    button_text_left_padding: 12,
                    button_text_top_padding: 3,
                    
                    // The event handler functions are defined in handlers.js
                    file_queued_handler : fileQueued,
                    file_queue_error_handler : fileQueueError,
                    file_dialog_complete_handler : fileDialogComplete,
                    upload_start_handler : uploadStart,
                    upload_progress_handler : uploadProgress,
                    upload_error_handler : uploadError,
                    upload_success_handler : uploadSuccess,
                    upload_complete_handler : uploadComplete,
                    queue_complete_handler : queueComplete	// Queue plugin event
                };

                swfu = new SWFUpload(settings);
             };
        </script>

        <style>
            #tagsbox {
                width: 75%;
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
        </style>
    </head>

    <body class="yui-skin-sam">
        <h1>Collage Photo Donation</h1>
        <form id="form1" action="/upload" method="POST" enctype="multipart/form-data">
            {% if error %}
                <span class="error">{{error}}</span>
            {% endif %}
            <p>Which photo would you like to upload? <!--<input class="box" type="file" name="vector"/>--></p>

            <div class="fieldset flash" id="fsUploadProgress">
            <input type="hidden" name="vector_ids" id="vector_ids" value=""/>
            <span class="legend">Upload Queue</span>
            </div>
            <div id="divStatus">0 Files Uploaded</div>
            <div>
                <span id="spanButtonPlaceHolder"></span>
                <input id="btnCancel" type="button" value="Cancel All Uploads" onclick="swfu.cancelQueue();" disabled="disabled" style="margin-left: 2px; font-size 8pt; height: 29px;"/>
            </div>

            <p>What is the title of your photo? <input class="box" type="text" name="title" size="50"/></p>
            <p>What tags best describe your photo? Click at least three tags on this list:
            <script type="text/javascript">
            {% include "tags.tpl" %}
            </script>
            <div id="tagsbox">
            </div>
            <p>How many hours may we hold your photo before uploading it to Flickr? Longer values increase our ability to store censored content.<input class="box" type="text" name="expiration" size="1" value="12"/> hours</p>
            <input type="submit" name="submit" value="Upload photo"/>
        </form>

        <form action="/upload_file" method="POST" enctype="multipart/form-data">
            <input type="file" name="vector"/>
            <input type="hidden" name="userid" value="{{userid}}"/>
            <input type="hidden" name="token" value="{{token}}"/>
            <input type="submit" value="Submit"/>
        </form>

        <a href="/logout">Logout</a>
    </body>
</html>
