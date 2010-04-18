<html>
    <head>
        <title>Collage Photo Donation</title>
    </head>

    <body>
        <form action="/process" method="POST" enctype="multipart/form-data">
            <p>Title: <input type="text" name="title"/></p>
            <p>File: <input type="file" name="vector"/></p>
            <p>Tags: <input type="text" name="tags"/></p>
            <p>Maximum holding time: <input type="text" name="expiration" value="86400"/></p>
            <input type="submit" name="submit" value="Upload photo"/>
        </form>
    </body>
</html>
