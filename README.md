# Maple Ave Movie Night Webapp


## **Introduction**:

Movienights at 57 Maple Ave. are recurring events that need some organisational overhead, such as inviting people, selecting movies, and performing movie a survey. In a quest for a standalone solution not involving Facebook and Co., the goal is to develop a Web Application able to carry out his overhead.


## **Technology**:

 [Django Webapp](https://www.djangoproject.com/start/), APIs as needed.


## **Specifications**:



*   MUST:
    *   Simple email-chain and email-database functionality, maybe [Mailchimp](https://developer.mailchimp.com/)
    *   Admin Accounts:
        *   Able to add movies.
        *   Able to create events.
        *   Able to send invitations.
    *   User Accounts:
        *   Able attend events (+ say which found they’re bringing)
        *   Able to vote for movies.
*   SHOULD:
    *   Automatic import of movie information via [omdbapi](http://www.omdbapi.com/).
        *   Displays the information in a standardized manner (title, director, year, duration, synopsis) → Duration should be used to create automatic calendar entry.
        *   Check availability on a few platforms (Netflix, Amazon, etc.)
    *   Blind voting mechanism to achieve fairness.
    *   Send reminder emails one day before and during the day of the event
    *   Send notifications to admins on attendance
*   OPTIONAL:
    *   Automatic proposition of movies based on theme / director / actor.
        *   That may be a little beyond our reach, unless we have access to a good database with some flags
    *   Cool analytics
        *   How often did you vote for a winning movie? → Users could win nerdy badges if the correctly predict the winner.
    *   Add automatic FB event which directs people on Webapp (for the lazy ones who would otherwise miss out). Probably doable with FB API.


## **Templates**:

[https://colorlib.com/wp/community-website-templates/](https://colorlib.com/wp/community-website-templates/)  (Flexipost and RS Sports in there)
