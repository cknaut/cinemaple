search_counter = 0;


// modidify raw json from TMDB to table html
function prep_movie_json(data) {
    // Convert Poster Path
    base_url = "https://image.tmdb.org/t/p/w200";

    pre_html = "<img src="
    post_html = "  >"


    for (var i = 0; i < data.length; i++) {
        if (data[i]["poster_path"] == null) {
            data[i]["poster_path"] = " <img  src='{% static 'userhandling/img/NAicon.svg' %}' >"
        } else {
            full_url = base_url.concat(data[i]["poster_path"]);
            data[i]["poster_path"] = pre_html.concat(full_url).concat(post_html)
        }
    }

    return data
}

function LoadDataTablesData(data) {

    // Add HTML Styling to JSON Data
    data = prep_movie_json(data);

    //Load  datatable
    var mov_table = $("#movietable");



    var column_name = ["Poster", "Title", "Synopsis", "Release Date", "Popularity", "Add data"];

    var num_col = column_name.length;

    if (search_counter == 0) {

        for (var i = 0; i < num_col; i++) {

            $('#movietable > thead tr').append('<th> '.concat(column_name[i]).concat('</th>'));
        }



        // Datatable without destroy option for first executions
        dat_tbl = mov_table.DataTable({
            "data": data,
            "order": [
                [4, "desc"]
            ],
            searching: false,
            "columns": [
                { "data": "poster_path" },
                { "data": "title" },
                { "data": "overview" },
                { "data": "release_date" },
                { "data": "popularity" },

            ],
        });

        $('#movietable tbody').on('click', 'tr', function() {
            var data = dat_tbl.row(this).data();

            url = tmdbimdb_movie_url_trunk.concat(data['id'])

            fetch(url)
                .then(response => {
                    return response.json()
                })
                .then(data => {
                    console.log(data);
                    LaunchMovieModal(data);

                })
                .catch(err => {
                    // Do something for an error here
                })
        });

    } else {
        dat_tbl = mov_table.DataTable({
            "data": data,
            searching: false,
            "order": [
                [4, "desc"]
            ],
            destroy: true,
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


function rep_null(input) {
    if (input == null) {
        input = "N/A";
    }
    return input
};

function LaunchMovieModal(data) {

    // Empty Modal
    $("#movieModalTitle").empty();
    $("#movieModalPoster").empty();
    $("#movieModalYear").empty();
    $("#movieModalCountry").empty();
    $("#movieModalDirector").empty();
    $("#movieModalActors").empty();
    $("#movieModalRuntime").empty();
    $("#movieModalPlot").empty();
    $("#trailerbutton").empty();



    // Title
    $("#movieModalTitle").append(data["tmdb_movie"]["title"]);

    // Poster
    base_url = "https://image.tmdb.org/t/p/w500";
    pre_html = "<img class='d-block w-100' src=\'"
    post_html = "\'   >"

    posterlink = pre_html.concat(base_url, data["tmdb_movie"]["poster_path"], post_html)
    $("#movieModalPoster").append(posterlink);

    // Check if trailer link is available and add it to href of button
    d_res = data["tmdb_link"]["results"];
    num_movies = d_res.length
    trailerlink = ""

    button_link = ""
    if (num_movies > 0) {
        for (var i = 0; i < num_movies; i++) {
            type = d_res[i]["type"]
            site = d_res[i]["site"]
            if (site == "YouTube" && type == "Trailer") {
                trailerlink = "http://www.youtube.com/embed/".concat(d_res[i]["key"])
                button_link = "<button type='button' class='btn btn-primary video-btn' data-src='".concat(trailerlink, "' > Watch Trailer  </button>")
            }


        }
    }

    if (button_link == "") {
        button_link = "<button type='button' class='btn btn-primary disabled'>No trailer available </button>"

    }

    $("#trailerbutton").append(button_link);



    // Change Link in Button.

    $("#movieModal").modal();

    $(document).ready(function() {

        // Gets the video src from the data-src on each button

        var $videoSrc;
        $('.video-btn').click(function() {
            $videoSrc = $(this).data("src");
            $("#video").attr('src', $videoSrc + "?autoplay=0&amp;modestbranding=1&amp;showinfo=0");
            $("#myModal").modal();
        });
        console.log($videoSrc);


        // stop playing the youtube video when I close the modal
        $('#myModal').on('hide.bs.modal', function(e) {
            // a poor man's stop video
            $("#video").attr('src', "");
        })

        // document ready
    });

    // Update Movie Infos
    $("#movieModalYear").append(remove_breaks(rep_null(data["imdb_movie"]["Year"])));
    $("#movieModalCountry").append(remove_breaks(rep_null(data["imdb_movie"]["Country"])));
    $("#movieModalDirector").append(remove_breaks(rep_null(data["imdb_movie"]["Director"])));
    $("#movieModalActors").append(remove_breaks(rep_null(data["imdb_movie"]["Actors"])));
    $("#movieModalRuntime").append(remove_breaks(rep_null(data["imdb_movie"]["Runtime"])));
    $("#movieModalPlot").append(remove_breaks(rep_null(data["imdb_movie"]["Plot"])));

    $("#movieModal").modal();

}


// Get input from textfield, call TMDB API, render Datatable
function find_movies() {
    console.log(search_counter);

    // Get query string
    var query = document.getElementById("querytitle").value;
    var year = document.getElementById("queryyear").value;

    if (query == "" || query == null) {

    } else {

        if (year == "") {
            url = tmdb_url_trunk.concat(query)
        } else {
            url = tmdb_url_trunk.concat(query, "/", year)
        }

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
}


const sleep = (milliseconds) => {
    return new Promise(resolve => setTimeout(resolve, milliseconds))
}


// Autp update doneTypingInterval ms after done typing
// Thanks to https://stackoverflow.com/questions/4220126/run-javascript-function-when-user-finishes-typing-instead-of-on-key-up
var typingTimer; //timer identifier
var doneTypingInterval = 200; //time in ms, 5 second for example
var $input = $('#querytitle, #queryyear');

//on keyup, start the countdown
$input.on('keyup', function() {
    clearTimeout(typingTimer);
    typingTimer = setTimeout(doneTyping, doneTypingInterval);
});

//on keydown, clear the countdown
$input.on('keydown', function() {
    clearTimeout(typingTimer);
});

//user is "finished typing," get movies
function doneTyping() {
    find_movies();
}


function remove_breaks(str) {
    return str.replace(/(\r\n|\n|\r)/gm, "");
}