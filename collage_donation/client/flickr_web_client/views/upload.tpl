<html>
    <head>
        <meta charset="UTF-8"/>
        <title>Collage Photo Donation</title>
        <link rel="stylesheet" type="text/css" href="http://yui.yahooapis.com/2.8.0r4/build/fonts/fonts-min.css" />
        <link rel="stylesheet" type="text/css" href="/static/button.css" />
        <script type="text/javascript" src="http://yui.yahooapis.com/2.8.0r4/build/yahoo-dom-event/yahoo-dom-event.js"></script>
        
        <script type="text/javascript" src="http://yui.yahooapis.com/2.8.0r4/build/element/element-min.js"></script>
        <script type="text/javascript" src="http://yui.yahooapis.com/2.8.0r4/build/button/button-min.js"></script>
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
        <form action="/upload" method="POST" enctype="multipart/form-data">
            %try:
                <span class="error">{{error}}</span>
            %except NameError:
                %pass
            %end
            <p>Which photo would you like to upload? <input class="box" type="file" name="vector"/></p>
            <p>What is the title of your photo? <input class="box" type="text" name="title" size="50"/></p>
            <p>What tags best describe your photo? Click at least three tags on this list:
            <script type="text/javascript">
            %include tags
            </script>
            <div id="tagsbox">
            </div>
            <p>How many hours may we hold your photo before uploading it to Flickr? Longer values increase our ability to store censored content.<input class="box" type="text" name="expiration" size="1" value="12"/> hours</p>
            <input type="submit" name="submit" value="Upload photo"/>
        </form>
        <a href="/logout">Logout</a>
    </body>
</html>
