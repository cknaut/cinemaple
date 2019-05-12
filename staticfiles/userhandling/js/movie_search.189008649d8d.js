search_counter = 0;

function LoadDataTablesData(data) {

    //Load  datatable
    var oTblReport = $("#movietable")



    var column_name = ["Title", "Release Date", "Synopsis", "Popularity", "Poster Path"];
    var thead = $("#movietable").find("thead");

    // Convert Poster Path
    base_url = "https://image.tmdb.org/t/p/w200";

    pre_html = "<img src="
    post_html = "  >"

    for (var i = 0; i < data.length; i++) {
        full_url = base_url.concat(data[i]["poster_path"]);
        data[i]["poster_path"] = pre_html.concat(full_url).concat(post_html)
    }

    var num_col = column_name.length;
    if (search_counter == 0) {
        for (var i = 0; i < num_col; i++) {
            $('<th>' + column_name[i] + '</th>').appendTo(thead);
        }

        // Datatable without destroy option for first executions
        oTblReport.DataTable({
            "data": data,
            destroy: true,
            searching: false,
            "columns": [
                { "data": "poster_path" },
                { "data": "title" },
                { "data": "overview" },
                { "data": "release_date" },
                { "data": "popularity" },

            ],
        });
    } else {
        // Datatable with destroy option for subsequent executions
        oTblReport.DataTable({
            "data": data,
            destroy: true,
            searching: false,
            "columns": [
                { "data": "poster_path" },
                { "data": "title" },
                { "data": "overview" },
                { "data": "release_date" },
                { "data": "popularity" },
            ],
        });
    }
    search_counter++;
}


function find_movies() {

    // Get query string
    var query = document.getElementById("query").value;
    var year = document.getElementById("year").value;

    // get JSON using wrapper on TMDB API
    { % if debug % }
    url_trunk = "http://127.0.0.1:8000/tmdb/"; { %
        else % }
    url_trunk = "http://www.cinemaple.com/tmdb/"; { % endif % }


    if (year == "") {
        url = url_trunk.concat(query)
    } else {
        url = url_trunk.concat(query, "/", year)
    }

    let data = [];

    fetch(url)
        .then(response => {
            return response.json()
        })
        .then(data => {
            // Build an new table.
            LoadDataTablesData(data["results"]);
            console.log(data);
        })
        .catch(err => {
            // Do something for an error here
        })
}


const sleep = (milliseconds) => {
    return new Promise(resolve => setTimeout(resolve, milliseconds))
}


$('input[type=text]').bind('input propertychange', function() {
    sleep(1000).then(() => {
        find_movies();
    })

});