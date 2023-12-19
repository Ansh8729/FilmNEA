import datetime
from . import db
from .models import Genres, LikedScreenplays, ScriptHas, Screenplays, FeaturedScripts
from flask_login import current_user
from datetime import datetime, timedelta

def LoadGenres():
    genrelist = ['Action', 'Adventure', 'Comedy', 'Drama', 'Fantasy', 'Horror', 'Musical', 'Mystery', 'Romance', 'Sci-Fi', 'Sports', 'Thriller', 'Western']
    for i in range(len(genrelist)):
            newgenre = Genres(genre=genrelist[i])
            db.session.add(newgenre)
            db.session.commit()
    for i in Genres.query.all():
            if i.genreid > 13:
                db.session.delete(i)
                db.session.commit()

def FeaturedExists(scriptid): #This function prevents duplicates from being enqueued
    query = FeaturedScripts.query.filter_by(scriptid = scriptid).first()
    if query:
        return True
    else:
        return False
    
def LoadFeatured(queue, date): 
    posts = Screenplays.query.filter_by(date_created = date) #Posts from today selected
    hour = 4
    for post in posts:
        likes = LikedScreenplays.query.filter(LikedScreenplays.scriptid == post.scriptid, LikedScreenplays.rating >= 4.0)
        if likes.count() >= 3 and FeaturedExists(post.scriptid) == False: #The screenplay is checked if it qualifies to be featured
            newfeatured = FeaturedScripts(scriptid = post.scriptid, dequeuedatetime = datetime.now()+timedelta(hours=hour))
            db.session.add(newfeatured)
            db.session.commit()
            hour += 4
    for num in range(1,7): #The first 6 records are enqueued from the database to the queue
        script = FeaturedScripts.query.filter_by(featuredid = num).first()
        queue[num-1] = script

def GiveRecommendations(writerid):
    posts = LikedScreenplays.query.filter(LikedScreenplays.rating > 3.5).all()
    postids = [] 
    for post in posts:
        if post.writerid == writerid:
            postids.append(post.scriptid) #The ScriptIDs of the posts the user has rated above 3.5 are stored in a list.

    if len(postids) == 0: #Validates if the query returned any data
        recs = None
        return recs
    else:
        genres = [] 
        for i in range(len(postids)):
            genreinfo = ScriptHas.query.filter(ScriptHas.scriptid == postids[i])
            for genre in genreinfo:
                genres.append(genre.genreid) #The GenreIDs of the liked posts are found

        finalgenres = []
        for i in range(len(genres)):
            genre2 = Genres.query.filter(Genres.genreid == genres[i])
            for genre in genre2:
                finalgenres.append(genre.genreid) 
        if (list(set(finalgenres)) == finalgenres and len(list(set(finalgenres))) > 1) or len(finalgenres) == 0:
            recs = None
            return recs
        else:
            favgenreid = max(set(finalgenres), key = finalgenres.count) #The GenreIDs are used to find the liked genre and then the user's most liked genre
            #If the user doesn't have a particular favourite, nothing is reccomended 

        favscripts = ScriptHas.query.filter(ScriptHas.genreid == favgenreid)
        genreids = []
        for script in favscripts:
            genreids.append(favscripts.scriptid) #The ScriptIDs whose posts are of the user's favourite genre are found
        
        likedids = []
        recs = []
        scripts = LikedScreenplays.query.all()
        for script in scripts:
            likedids.append(script.scriptid)
        for id in genreids:
            if (id not in likedids): #Only the posts that haven't been liked by the user yet are shown as reccomendations.
                script = Screenplays.query.filter(Screenplays.scriptid == id).first()
                if script.writer.user.id != current_user.id:
                    recs.append(script)
        return recs