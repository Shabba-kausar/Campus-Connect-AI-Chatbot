$(document).ready(function() {
    // Variables
    let isFormSubmitted = false;
    let hasResponded = false;
    let storedName = localStorage.getItem('name');
    let storedPhone = localStorage.getItem('phone');
    let userId = localStorage.getItem('user_id');
    let isTyping = false;
    
    // Quick replies for common questions
    const quickReplies = [
        "Tell me about admission",
        "What clubs are available?",
        "Hostel facilities",
        "Exam schedule",
        "Canteen information"
    ];

    // Toggle chatbot visibility
    $('.chat-toggle-btn').click(function() {
        $('#chatbot-container').toggle();
        
        // If first time opening or no stored user details
        if (!hasResponded) {
            setTimeout(function() {
                showWelcomeMessage();
                hasResponded = true;
                
                if (!storedName || !storedPhone) {
                    setTimeout(function() {
                        showForm();
                    }, 1000);
                } else {
                    setTimeout(function() {
                        addMessage(`Welcome back, ${storedName}! How can I assist you today?`, false);
                        showQuickReplies();
                        isFormSubmitted = true;
                    }, 1000);
                }
            }, 500);
        }
    });

    // Close chatbot
    $('.close-btn').click(function() {
        $('#chatbot-container').hide();
    });

    // Add message to chat
    function addMessage(message, isUser, withTimestamp = true) {
        const messageClass = isUser ? 'user-message' : 'bot-message';
        let messageHTML = `<div class="${messageClass}">${message}`;
        
        if (withTimestamp) {
            const now = new Date();
            const timeString = now.getHours() + ':' + (now.getMinutes() < 10 ? '0' : '') + now.getMinutes();
            messageHTML += `<div class="message-timestamp">${timeString}</div>`;
        }
        
        messageHTML += '</div>';
        
        $('#chat-content').append(messageHTML);
        scrollToBottom();
    }

    // Show welcome message
    function showWelcomeMessage() {
        const welcomeMessage = "Hi there! 👋 I'm the JEC AI Assistant. I can help you with information about Jorhat Engineering College.";
        addMessage(welcomeMessage, false);
    }

    // Show typing indicator
    function showTypingIndicator() {
        if (!isTyping) {
            isTyping = true;
            $('#chat-content').append('<div class="typing-indicator" id="typing-indicator"><span></span><span></span><span></span></div>');
            scrollToBottom();
        }
    }

    // Hide typing indicator
    function hideTypingIndicator() {
        isTyping = false;
        $('#typing-indicator').remove();
    }

    // Scroll to bottom of chat
    function scrollToBottom() {
        $('#chat-content').scrollTop($('#chat-content')[0].scrollHeight);
    }

    // Show form for user details
    function showForm() {
        const formHTML = `
            <div class="bot-message">
                <p>To provide you with personalized assistance, could you please share your name and phone number?</p>
                <form id="user-details-form">
                    <h3>Your Details</h3>
                    <input type="text" id="name" name="name" placeholder="Enter your name" required>
                    <input type="text" id="phone" name="phone" placeholder="Enter your phone number" required>
                    <button type="submit">Submit</button>
                </form>
            </div>`;
        $('#chat-content').append(formHTML);
        scrollToBottom();
    }

    // Show quick replies
    function showQuickReplies() {
        let quickRepliesHTML = '<div class="quick-replies">';
        quickReplies.forEach(reply => {
            quickRepliesHTML += `<div class="quick-reply">${reply}</div>`;
        });
        quickRepliesHTML += '</div>';
        
        $('#chat-content').append('<div class="bot-message">Here are some topics you might be interested in:<div class="quick-replies">' + quickRepliesHTML + '</div></div>');
        scrollToBottom();
    }

    // Send button click
    $('#send-btn').click(function() {
        sendMessage();
    });

    // Enter key press in input
    $('#chat-input').keypress(function(e) {
        if (e.which == 13) {
            sendMessage();
            return false;
        }
    });

    // Click on quick reply
    $(document).on('click', '.quick-reply', function() {
        const replyText = $(this).text();
        $('#chat-input').val(replyText);
        sendMessage();
    });

    // Send message function
    function sendMessage() {
        const userInput = $('#chat-input').val().trim();
        
        if (userInput === '') return;
        
        if (!isFormSubmitted && !storedName && hasResponded) {
            addMessage("Please fill in your details before we continue.", false);
            return;
        }

        // Add user message to chat
        addMessage(userInput, true);
        $('#chat-input').val('');
        
        // If we have responded but form not submitted, show form
        if (hasResponded && !isFormSubmitted && !storedName) {
            showForm();
            return;
        }
        
        // Process user message and get bot response
        showTypingIndicator();
        
        // Make Ajax call to the backend
        $.ajax({
            type: 'POST',
            url: '/api/message/',
            contentType: 'application/json',
            data: JSON.stringify({ 
                message: userInput,
                user_id: userId,
                name: storedName,
                phone: storedPhone
            }),
            success: function(response) {
                setTimeout(function() {
                    hideTypingIndicator();
                    addMessage(response.message, false);
                    
                    // Store user ID if not already stored
                    if (!userId) {
                        userId = response.user_id;
                        localStorage.setItem('user_id', userId);
                    }
                }, 1000); // Delay to simulate typing
            },
            error: function(error) {
                setTimeout(function() {
                    hideTypingIndicator();
                    addMessage("I'm sorry, I'm having trouble connecting to my brain. Please try again later.", false);
                }, 1000);
                console.error("Error:", error);
            }
        });
    }

    // User details form submission
    $(document).on('submit', '#user-details-form', function(e) {
        e.preventDefault();
        const name = $('#name').val();
        const phone = $('#phone').val();

        if (name && phone) {
            localStorage.setItem('name', name);
            localStorage.setItem('phone', phone);
            storedName = name;
            storedPhone = phone;
            isFormSubmitted = true;
            
            $('#user-details-form').closest('.bot-message').remove();
            addMessage(`Thank you, ${name}! I'll remember you next time. How can I help you with information about JEC?`, false);
            showQuickReplies();
        }
    });

    // Add feedback on bot messages
    $(document).on('mouseenter', '.bot-message', function() {
        if (!$(this).find('.message-feedback').length) {
            $(this).append('<div class="message-feedback"><button class="feedback-btn feedback-helpful"><i class="fas fa-thumbs-up"></i></button><button class="feedback-btn feedback-unhelpful"><i class="fas fa-thumbs-down"></i></button></div>');
        }
    });

    $(document).on('mouseleave', '.bot-message', function() {
        if (!$(this).hasClass('feedback-submitted')) {
            $(this).find('.message-feedback').remove();
        }
    });

    $(document).on('click', '.feedback-helpful, .feedback-unhelpful', function() {
        const feedbackType = $(this).hasClass('feedback-helpful') ? 'helpful' : 'unhelpful';
        const messageElement = $(this).closest('.bot-message');
        messageElement.addClass('feedback-submitted');
        
        $(this).closest('.message-feedback').html(`<span style="font-size: 11px; color: var(--primary-color);">${feedbackType === 'helpful' ? 'Thanks for your feedback!' : 'Thanks! I\'ll try to improve.'}</span>`);
        
        // Here you could send feedback to the server if desired
        // $.ajax({
        //     type: 'POST',
        //     url: '/api/feedback/',
        //     data: { 
        //         message_id: messageId, 
        //         feedback: feedbackType 
        //     }
        // });
    });
}); 