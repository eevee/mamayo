<!DOCTYPE html>
<html>
<head>
    <meta charset="utf8">
    <script src="//ajax.googleapis.com/ajax/libs/jquery/1.8.3/jquery.min.js"></script> 
    ## XXX this is so rude
    <script src="http://www.flotcharts.org/javascript/jquery.flot.min.js"></script>
    <script src="http://www.flotcharts.org/flot/jquery.flot.time.js"></script>

    <script type="text/javascript">
        $(function() {
            $.plot('#requests-histogram', ${flot_data}, {
                xaxis: {
                    mode: "time",
                    timezone: "browser",
                },
                yaxis: {
                    min: 0,
                    minTickSize: 1,
                },
                series: {
                    bars: {
                        show: true,
                        fill: true,
                        // width is 30 seconds
                        barWidth: 30 * 1000,
                    },
                },
            });
        });
    </script>

    <link rel="stylesheet" type="text/css" href="http://beta.veekun.com/css/archetype.css">
    <style type="text/css">
        body {
            font-family: Ubuntu, "DejaVu Sans", Arial, sans-serif;
            font-size: 14px;
            background: white;
            color: #202020;
            margin: 0;
            padding: 0;
        }
        body > header {
            font-size: 2em;
            margin: 0 0 0.5em;
            padding: 0;
            background: #ececec;
        }
        body > header ol {
            margin: 0;
            padding: 0;
            list-style-type: none;
        }
        body > header ol > li {
            display: inline-block;
            padding: 0.5em;
            padding-right: 2em;
        }

        section {
            margin: 1em;
        }

        #requests-histogram {
            height: 300px;
            width: 400px;
        }
    </style>
</head>
<body>
    <header>
        <nav>
            <ol>
                <li>mamayo status</li>
                <li>${app.name}</li>
            </ol>
        </nav>
    </header>

    <section>
        <dl class="horizontal">
            <dt>Mounted at</dt>
            <dd>${app.path.path}</dd>
            <dt>Status</dt>
            <dd>
                % if app.running:
                Running
                % else:
                Not running
                % endif
            </dd>
            <dt>Requests served</dt>
            <dd>${app.requests_finished}</dd>
            <dt>Requests histogram</dt>
            <dd>
                <div id="requests-histogram"></div>
            </dd>
        </dl>

        <form method="POST" action="">
            <button type="submit" name="action" value="respawn">Respawn runner</button>
        </form>
    </section>

    <footer>

    </footer>
</body>
</html>
