$(document).ready(function() {
    var csrftoken = $('meta[name="csrf-token"]').attr('content');

    $('.reaction-button').on('click', function() {
        var reaction = $(this).data('reaction');
        var reactUrl = $('.post-reactions').data('react-url');
        
        $.ajax({
            url: reactUrl,
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ reaction: reaction }),
            headers: {
                'X-CSRFToken': csrftoken
            },
            success: function(data) {
                if (data.status === 'success') {
                    console.log('Reaction recorded:', data.reaction);
                    // Update the UI with new reaction counts if needed
                } else {
                    console.error('Failed to record reaction:', data.message);
                }
            },
            error: function(xhr, status, error) {
                console.error('Error:', error);
            }
        });
    });
});

$(document).ready(function() {
    // Get the CSRF token from the meta tag
    var csrftoken = $('meta[name="csrf-token"]').attr('content');

    // Handle form submission for comments
    $('#comment-form').on('submit', function(e) {
        e.preventDefault(); // Prevent the default form submission

        var content = $(this).find('textarea[name="content"]').val();
        var postUrl = window.location.href; // URL to submit the comment to

        $.ajax({
            url: postUrl,
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ content: content }),
            headers: {
                'X-CSRFToken': csrftoken
            },
            success: function(data) {
                if (data.status === 'success') {
                    // Append the new comment to the list
                    $('#comments-list').append(
                        '<div class="comment">' +
                            '<div class="comment-author">' +
                                '<div class="author-info">' +
                                    '<strong>' + data.username + '</strong> <small>' + data.created_at + '</small>' +
                                '</div>' +
                            '</div>' +
                            '<p>' + content + '</p>' +
                        '</div>'
                    );
                    // Clear the textarea
                    $('#comment-form textarea').val('');
                } else {
                    console.error('Failed to post comment:', data.message);
                }
            },
            error: function(xhr, status, error) {
                console.error('Error:', error);
            }
        });
    });
});
