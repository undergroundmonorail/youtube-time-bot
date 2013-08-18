import praw  # Python Reddit Api Wrapper (dft.ba/-praw) by /u/bboe, handles API requests so I don't have to
import re
from requests import ConnectionError
from random import choice
from time import sleep

def quick_url(comment):  # 100% stolen from /u/bboe's alert.py (dft.ba/-alert-py), part of prawtools.
    # Return the URL for the comment without fetching its submission.
    def to_id(fullname):
        return fullname.split('_', 1)[1]
    return ('http://www.reddit.com/r/{0}/comments/{1}/_/{2}?context=1'
            .format(comment.subreddit.display_name, to_id(comment.link_id),
                    comment.id))

def footer():
    # Choose a snarky message to add to the end of each comment.
    return "\n____\n^^{}".format(choice(footers).replace(' ', '&nbsp;').format(username))

def matches_regex(full_string, substring):
    r = '\[.*{}.*\]\(.*\)'
    m = re.search(r.format(substring), full_string)
    if m is None:
        return True
    return False
        
###MAIN###

username = 'INSERT BOT USERNAME'
password = 'INSERT BOT PASSWORD'

owner_username = 'INSERT OWNER USERNAME'

subreddit =  'WHATEVER SUBREDDIT IDC'  # Choose what subreddit to look at.
                                       # Could be multiple subreddits ('foo+bar')
                                       # Or all subreddits ('all')
                           
with open('footers', 'r') as file:  # Load the list of snarky comments to end the comment with
    footers = file.read().split('\n')

r = praw.Reddit('Youtube Time Linker v1.0 by /u/undergroundmonorail')  # Create the connection to reddit.
print "Connection to reddit made"

while True:
    try:
        r.login(username, password)  # Log in with the bot's username and password
        print "Logged in"
        break
    except ConnectionError:
        print "No response from reddit, sleeping..."
        sleep(30)  # If reddit is currently inaccessible, wait for 30 seconds before trying to connect again.

with open('already_done', 'r') as file:  # Load the logs to memory
    already_done = file.read().split('\n')
print "Logs loaded:"
print already_done

while True:
    try:
        comments = r.get_subreddit(subreddit).get_comments()  # Get the 25 most recent comments from the subreddit
        print "Comments retrieved"
        
        for comment in comments:
            m = re.finditer('(([0-5]?\d:)?[0-5])?\d:[0-5]\d', comment.body)  # This regex matches every time in the comment, in these formats:
                                                                             # *     m:ss
                                                                             # *    mm:ss
                                                                             # *  h:mm:ss
                                                                             # * hh:mm:ss
                                                                            
            if not comment.id in already_done:  # If the bot's already looked at this comment, ignore it. (I don't account for edited comments)
            
                already_done.append(comment.id)
                while len(already_done) > 50:
                    already_done.pop(0)                  # Add the current comment to the list of comments the bot has seen, both
                with open('already_done', 'w') as file:  # in the memory and to disk. This means we won't waste time scanning it
                    for id in already_done:              # later.
                        file.write("{}\n".format(id))
                    
                if m is not None and comment.submission.domain == "youtube.com" and not comment.author.name.lower() == username.lower():
                    print "----\nComment found\nComment ID:",
                    print comment.id
                    print "Comment body:",
                    print comment.body
                    rep = ""  # This string eventually becomes the comment that we post.
                              # It's defined outside of the loop for scope reasons.
                                             
                    for match in m:  # "for match in m" means "for every time we found in the comment"
                    
                        if not matches_regex(comment.body, match.group()):  # Check if the string matches the regex
                            print "Regex not matched, ignoring"
                        else:
                            time = match.group()  # Keep the time as a string
                            print "Time isolated:",
                            print time
                            time_c = time.split(':')  # Split the time into a list of strings.
                                                      # Every time we reference this list, we use
                                                      # time_c[::-1], reversing the order.
                                                      # This means that we have easy access to the number
                                                      # of seconds, minutes and hours in the time in
                                                      # ascending order.
                                                                      
                            time_s = (int(time_c[::-1][0]) + int(time_c[::-1][1]) * 60) # time_s is an int that stores the total
                                                                                        # number of seconds in the time.
                                                                                        # seconds + (minutes * 60) = total_seconds
                                                                                        
                            if len(time_c) == 3:                                        # If the time included hours, we have to handle those too.
                                time_s += int(time_c[::-1][2]) * 3600                   # seconds + (hours * 3600) = total_seconds
                            print "Time in seconds:",
                            print time_s
                            rep = "{} [{}]({}#t={}s)".format(rep, time, comment.submission.url, time_s) # Updates the comment body to include
                                                                                                        # the current running comment (if it exists)
                                                                                                        # and the link for the new time
                    if rep != "":                                  # If there's a comment to write at all,
                        reply = comment.reply(rep[1:] + footer())  # write it with the footer at the end.
                        print "Comment posted:",                   # Additionally, strip the leading space
                        print quick_url(reply)                     # because it bothers me.

        print "----\nAll comments scraped.\nChecking mail"

        for message in r.get_unread(unset_has_mail=True, update_user=True):
            print "----\nMessage found"
            if message.was_comment == True:   # For every unread message, in the mailbox, check if it's a comment.
                print "Message is a comment"  # If it is, send me a message with the text of and link to the comment.
                r.send_message(owner_username, "Comment reply from {}".format(message.author.name),
                "{}\n\n[[x]](http://www.reddit.com{})".format(message.body, message.context))
            else:
                print "Message is a PM"  # If it's a private message, send me a message with the subject and body
                                         # of the message, and a link to reply.
                r.send_message(owner_username, "Message from {}".format(message.author.name),
                "**Subject:** {}\n\n**Body:** {}\n\n[[x]](http://www.reddit.com/message/compose/?to={}&subject=Re: {})".format(message.subject, message.body, message.author.name, message.subject))
            message.mark_as_read()

    except ConnectionError:
        print "No response from reddit, sleeping..."
        sleep(30)  # Again, sleep for 30 seconds before checking if reddit's back up.