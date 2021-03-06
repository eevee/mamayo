<!DOCTYPE html>
<html>
<head>
    <meta charset="utf8">
    <script src="/.well-known/mamayo/static/js/jquery-1.8.3.js"></script>
    <script src="/.well-known/mamayo/static/js/jquery.flot-0.7.js"></script>

    <script type="text/javascript">
        var histogram_size = ${app.HISTOGRAM_BUCKET_SIZE};
        var histogram_options = {
            xaxis: {
                mode: "time",
                timezone: "browser",
                minTickSize: [histogram_size, "second"],
            },
            yaxis: {
                min: 0,
                minTickSize: 1,
            },
            series: {
                bars: {
                    show: true,
                    fill: true,
                    barWidth: histogram_size * 1000,
                },
            },
        };
        var histogram_redraw = function(data) {
            $.plot('#requests-histogram', data, histogram_options);
        };

        $(function() {
            histogram_redraw(${flot_data});
        });

        setInterval(function() {
                $.getJSON('/.well-known/mamayo/${app.name}/chartdata.json')
                .done(histogram_redraw);
            },
            histogram_size * 1000
        );

    </script>

    <link rel="stylesheet" type="text/css" href="/.well-known/mamayo/static/css/archetype.css">
    <style type="text/css">
        /* defeat archetype oops */
        table {
            width: auto;
        }

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
                % if app.failed:
                Failed to start
                % elif app.failing:
                Failing to start
                % elif app.running:
                Running
                % else:
                Starting
                % endif
            </dd>
            % if log_size is not None:
            <dt>Gunicorn log</dt>
            <dd><a href="${app.name}/log">${log_size} bytes</a></dd>
            % endif
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
