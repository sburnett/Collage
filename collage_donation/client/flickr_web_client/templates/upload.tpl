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
                        upload_target : "divFileProgressContainer",
                        progressTarget : "fsUploadProgress",
                        cancelButtonId : "btnCancel"
                    },
                    debug: false,

                    // Button settings
				    button_image_url : "/static/images/SmallSpyGlassWithTransperancy_17x18.png",
                    button_width: "250",
                    button_height: "18",
                    button_placeholder_id: "spanButtonPlaceHolder",
                    button_text : '<span class="button">Select images to upload<span class="buttonSmall">(10 MB Max)</span></span>',
                    button_text_style : '.button { font-family: Helvetica, Arial, sans-serif; font-size: 12pt; } .buttonSmall { font-size: 10pt; }',
                    button_text_top_padding: 0,
                    button_text_left_padding: 18,
                    button_window_mode: SWFUpload.WINDOW_MODE.TRANSPARENT,
                    button_cursor: SWFUpload.CURSOR.HAND,

                    
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

                val = document.getElementById("vector_ids").value;
                if(val.length > 0) {
                    filenames = val.split(";");
                    for(var i = 0; i < filenames.length; i++) {
                        url = "/thumbnail?filename=" + escape(filenames[i]);
                        addImage(url, filenames[i]);
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
            <div style="display: inline; border: solid 1px #7FAAFF; background-color: #C5D9FF; padding: 2px;">
                <span id="spanButtonPlaceHolder"></span>
            </div>
            <div id="divFileProgressContainer" style="height: 75px;"></div>
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
