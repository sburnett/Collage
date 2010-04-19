<html>
    <head>
        <title>Collage Photo Donation</title>
    </head>

    <body>
        <form action="/upload" method="POST" enctype="multipart/form-data">
            %try:
                <p>Error: {{error}}</p>
            %except NameError:
                %pass
            %end
            <p>Title: <input type="text" name="title"/></p>
            <p>File: <input type="file" name="vector"/></p>
            <p>Tags: <input type="text" name="tags"/></p>
            Please try to use at least two of these tags:
            %include tags
            <p>Maximum holding time: <input type="text" name="expiration" value="86400"/></p>
            <input type="submit" name="submit" value="Upload photo"/>
        </form>
        <a href="/logout">Logout</a>
    </body>
</html>
