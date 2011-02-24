<html>
    <style>
        body {
            font-family: sans-serif;
        }
        div {
            width: 100%;
        }
        div.box {
            border: 1px solid gray;
            border-bottom: 0px;
            padding: 2px;
        }
        iframe#articles {
            height: 150;
            overflow: auto;
            width: 100%;
        }
        div#queued {
            height: 128px;
            overflow: hidden;
        }
        div#embedding {
            height: 128px;
            overflow: hidden;
        }
        div#uploaded {
            height: 128px;
            overflow: hidden;
        }
        img {
            float: left;
        }
        b {
            clear: both;
            display: block;
            font-size: 1.3em;
        }
    </style>
    <head>
        <title>Collage Server Visualization</title>
        <script type="text/javascript" src="/static/jquery.js"></script>
        <script type="text/javascript">
            $(document).ready(function() {
                window.setInterval('pollForUpdates()', 1000);
            });

            var story_id = -1;
            var queued_id = -1;
            var embedding_id = -1;
            var uploaded_id = -1;

            function fadeInImage(name, id, ident, append) {
                var img = new Image();
                $(img).load(function() {
                    $(this).hide();
                    if(append) {
                        $('#' + name).append(this);
                    } else {
                        $('#' + name).prepend(this);
                    }

                    $(this).fadeIn("slow");
                })
                .attr('src', '/' + name + '?id=' + id)
                .attr('ident', ident);
            }

            function fadeDownImage(name, ident) {
                $("#" + name + " > img[ident='" + ident + "']")
                    .css('position', 'relative')
                    .animate({'top': '+=50px', 'opacity': 0}, 'slow', function () {
                        $("#" + name + " > img[ident='" + ident + "']").remove()
                    });
            }

            function pollForUpdates() {
                $.post("/update", {story_id: story_id,
                                   queued_id: queued_id,
                                   embedding_id: embedding_id,
                                   uploaded_id: uploaded_id}, function(xml) {
                    $(xml).find("refresh").each(function() {
                        window.location.reload(true);
                    });

                    $(xml).find("story").each(function() {
                        $("#articles").attr('src', '/article?id=' + $(this).attr("id"));
                        story_id = Math.max(story_id, $(this).attr("id"));
                    });

                    $(xml).find("queued").each(function() {
                        fadeInImage('queued', $(this).attr("id"), $(this).attr("identifier"), true);

                        queued_id = Math.max(queued_id, $(this).attr("id"));
                    });

                    $(xml).find("embedding").each(function() {
                        fadeDownImage('queued', $(this).attr("identifier"));
                        $("#embedding > img[ident='" + $(this).attr("identifier") + "']").remove();

                        fadeInImage('embedding', $(this).attr("id"), $(this).attr("identifier"), true);

                        embedding_id = Math.max(embedding_id, $(this).attr("id"));
                    });

                    $(xml).find("uploaded").each(function() {
                        $("#queued > img[ident='" + $(this).attr("identifier") + "']").remove();
                        fadeDownImage('embedding', $(this).attr("identifier"));
                        $("#uploaded > img[ident='" + $(this).attr("identifier") + "']").remove();

                        fadeInImage('uploaded', $(this).attr("id"), $(this).attr("identifier"), false);

                        uploaded_id = Math.max(uploaded_id, $(this).attr("id"));
                    });
                });
            }
        </script>
    </head>

    <body>
        <div class="box">
        <b>Censored News Articles</b>
        <iframe id="articles">
        </iframe>
        </div>

        <div class="box">
        <b>Photos Queued for Upload</b>
        <div id="queued">
        </div>
        </div>

        <div class="box">
        <b>Currently Embedding with Censored Articles</b>
        <div id="embedding">
        </div>
        </div>

        <div class="box" style="border-bottom: 1px solid gray">
        <b>Embedded Photos on User-Generated Content Host</b>
        <div id="uploaded">
        </div>
        </div>
    </body>
</html>
