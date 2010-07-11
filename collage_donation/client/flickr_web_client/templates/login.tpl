<html>
    <head>
        <title>Collage Flickr Photo Donation</title>
        <link rel="stylesheet" type="text/css" href="http://yui.yahooapis.com/2.8.0r4/build/fonts/fonts-min.css" />
        <link rel="stylesheet" type="text/css" href="/static/default.css" />
    </head>
    <body>
        <h1>Collage Flickr Photo Donation</h1>

        Welcome to Collage Photo Donation. Using this Web site, you
        can upload photos to your Flickr account. In the process of doing so,
        you will also be helping users of <a
        href="http://www.gtnoise.net/collage">Collage</a>, a new system for
        circumventing Internet censorship.

        <h2>How does it work?</h2>

        All you have to do is upload your photos to Collage Photo Donation.
        Once we have your photos, we hide pieces of censored Web pages inside
        them. These are Web pages blocked by regimes that censor Internet
        access, like China and Iran. This process does not perceptibly modify
        the visual content of your photos. Afterward, we upload the photos to
        your Flickr account on your behalf. Everyone wins: You get to share your
        photos on Flickr and simultaneously help defeat Internet censorship, and
        users of <a href="http://www.gtnoise.net/collage">Collage</a> can read
        Web pages from behind restrictive Internet firewalls.

        <p><img src="/static/images/overview.png"/></p>

        <h2>Who can use it?</h2>

        Anybody with a Flickr account can donate photos. If you don't have a
        Flickr account, you can <a href="http://www.flickr.com/signup">sign up
        for one</a>.

        <h2>How do I get started?</h2>

        <p>To begin, you must <a href="{{login_url}}">log in</a> using your
        Flickr account. If you haven't used Collage Photo Donation before
        you will be asked to authorize Collage to access your Flickr account.
        This will allow us to upload your photos to your Flickr account on your
        behalf.</p>

        <input type="button" value="Log in" onclick="window.open('{{login_url}}', '_self');"/>
    </body>
</html>
