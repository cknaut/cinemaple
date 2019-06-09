search_counter = 0;
movie_counter = 1;

// modidify raw json from TMDB to table html
function prep_movie_json(data) {
    // Convert Poster Path
    base_url = "https://image.tmdb.org/t/p/w200";

    pre_html = "<img src="
    post_html = "  >"


    for (var i = 0; i < data.length; i++) {
        if (data[i]["poster_path"] == null) {
            data[i]["poster_path"] = " <button type='button' class='btn btn-primary disabled'>No poster available. </button>"
        } else {
            full_url = base_url.concat(data[i]["poster_path"]);
            data[i]["poster_path"] = pre_html.concat(full_url).concat(post_html)
        }
        data[i]["button"] = "<button type='button' value=" + data[i]["id"] + " class='btn btn-primary addbutton'>Add </button> <button value=" + data[i]["id"] + "  type='button' class='btn btn-primary showbutton'>Info </button>"
    }

    return data
}

function LoadDataTablesData(data) {

    // Add HTML Styling to JSON Data
    data = prep_movie_json(data);

    //Load  datatable
    var mov_table = $("#movietable");



    var column_name = ["Poster", "Title", "Synopsis", "Release Date", "Popularity", "Controls"];

    var num_col = column_name.length;

    if (search_counter == 0) {
        // build header
        for (var i = 0; i < num_col; i++) {

            $('#movietable > thead tr').append('<th> '.concat(column_name[i]).concat('</th>'));
        }

        // Datatable without destroy option for first executions
        dat_tbl = mov_table.DataTable({
            "data": data,
            responsive: true,
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
                { "data": "button" },

            ],
        });

    } else {
        dat_tbl = mov_table.DataTable({
            "data": data,
            searching: false,
            responsive: true,
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
                { "data": "button" },

            ],
        });
    }

    search_counter++;
}

function initiate_datatables_buttons() {
    $(".showbutton").click(function() {
        var id = $(this).attr('value');
        url = tmdbimdb_movie_url_trunk.concat(id)

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

    // thanks https://stackoverflow.com/questions/20054889/button-onclick-function-firing-twice
    $('.addbutton').unbind('click').click(function() {
        var id = $(this).attr('value');
        movie_already_added = check_movie_input(id)
        if (movie_already_added) {
            $("#modalMovieAlreadyAdded").modal();
            return
        }
        movieaddfield = "#id_form2-movieID" + movie_counter
        $(movieaddfield).val(id);
        $("#advisealert").hide()
        $("#movieaddSuccess").modal();

        url = tmdbimdb_movie_url_trunk.concat(id)

        fetch(url)
            .then(response => {
                return response.json()
            })
            .then(data => {
                console.log(data);
                AddMovie(data);

            })
            .catch(err => {
                // Do something for an error here
            })

    });
}


function AddMovie(data) {
    title = data["title"]
    year = data["Year"]
    director = data["Director"]
    runtime = data["Runtime"]
    id = data["id"]

    movie_alert = generate_movie_alert(title, year, director, runtime, id)
    $("#moviealerts").append(movie_alert);

    movie_counter = movie_counter + 1

    $(".movieclosebutton").unbind('click').click(function() {
        var id = $(this).attr('value');
        movie_counter = movie_counter - 1
        remove_and_reorder_movies(id)
    });

}

function check_movie_input(id) {
    // after clicking the add movie button, check if movie id alreay enterd in a movie text field.
    error = false
    for (var i = 1; i < 10; i++) {
        movieaddfield = "#id_form2-movieID" + i;
        if ($(movieaddfield).val() == id) {
            error = true
        }
    }

    return error

}



function remove_and_reorder_movies(id) {
    // when a movie is removed, remove ID from formfield and move following movies up to new movies can be appended.

    pos_movie_removed = 0 // index of movie to be removed

    // remove id 
    for (var i = 1; i < 11; i++) {
        movieaddfield = "#id_form2-movieID" + i;
        if ($(movieaddfield).val() == id) {
            $(movieaddfield).val("")
            pos_movie_removed = i
        }
    }

    // move movies afer removed ID one up
    for (var i = pos_movie_removed; i < 11; i++) {
        movieaddfield = "#id_form2-movieID" + i;
        next_index = i + 1
        movieaddfield_next = "#id_form2-movieID" + next_index;
        next_val = $(movieaddfield_next).val()
        $(movieaddfield).val(next_val) //set value of next field))
    }
}



function generate_movie_alert(title, year, director, runtime, mov_id) {
    // generate html displaying the movie alert
    movie_alert = "<div class='alert alert-success alert-dismissible fade show moviealert' role='alert'> <strong>" + title + "</strong>, (" + year + "), Director: " + director + ", Runtime: " + runtime + "<button type='button' value=" + mov_id + " class='close movieclosebutton' data-dismiss='alert' aria-label='Close' > <span aria-hidden='true'> &times; </span></button> </div>"
    return movie_alert
}

function rep_null(input) {
    if (input == null || input == "") {
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
    $("#movieModalProducer").empty();
    $("#movieModalActors").empty();
    $("#movieModalRuntime").empty();
    $("#movieModalPlot").empty();
    $("#trailerbutton").empty();
    $("#moviemodaladdbutton").val("");

    // Title
    $("#movieModalTitle").append(data["title"]);


    $("#moviemodaladdbutton").val(data["id"]);


    // Poster
    base_url = "https://image.tmdb.org/t/p/w500";
    pre_html = "<img class='d-block w-100' src=\'"
    post_html = "\'   >"

    if (data["poster_path"] == null) {
        posterlink = " <button type='button' class='btn btn-primary disabled'>No poster available. </button> "
    } else {
        posterlink = pre_html.concat(base_url, data["poster_path"], post_html)
    }

    $("#movieModalPoster").append(posterlink);

    //set trailerlink
    if (data["Trailerlink"] == "") {
        button_link = "<button type='button' class='btn btn-primary disabled'>No trailer available. </button>"
    } else {
        button_link = "<button type='button' class='btn btn-primary video-btn' data-src='".concat(data["Trailerlink"], "' > Watch Trailer  </button>")
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
    $("#movieModalYear").append(remove_breaks(rep_null(data["Year"])));
    $("#movieModalCountry").append(remove_breaks(rep_null(data["Country"])));
    $("#movieModalDirector").append(remove_breaks(rep_null(data["Director"])));
    $("#movieModalProducer").append(remove_breaks(rep_null(data["Producer"])));
    $("#movieModalActors").append(remove_breaks(rep_null(data["Actors"])));
    $("#movieModalRuntime").append(remove_breaks(rep_null(data["Runtime"])));
    $("#movieModalPlot").append(remove_breaks(rep_null(data["Plot"])));

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


// Initialize Buttons after each redraw of table.
$('#movietable').on('draw.dt', function() {
    initiate_datatables_buttons()
});