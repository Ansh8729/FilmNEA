import datetime
from . import db
from .models import Genres, LikedScreenplays, ScriptHas, Screenplays, FeaturedScripts
from flask_login import current_user
from datetime import datetime, timedelta

def LoadGenres(): #Adds the genres to the database when the database is created
    genrelist = ['All','Action', 'Adventure', 'Comedy', 'Drama', 'Fantasy', 'Horror', 'Musical', 'Mystery', 'Romance', 'Sci-Fi', 'Sports', 'Thriller', 'Western']
    for i in range(len(genrelist)):
            newgenre = Genres(genre=genrelist[i])
            db.session.add(newgenre)
            db.session.commit()
    for i in Genres.query.all(): # Removes duplicate additions from the list of genres
            if i.genreid > 14:
                db.session.delete(i)
                db.session.commit()

def ScriptInFeatured(scriptid): #Checks if a script is already in the featured screenplay queue
    query = FeaturedScripts.query.filter_by(scriptid = scriptid).first()
    if query:
        return True
    else:
        return False
    
def LoadFeatured(queue, date): #Loads the queue with 6 screenplays that got 10 or more ratings of 4 stars or more that day
    posts = Screenplays.query.filter_by(date_created = date) 
    hour = 4
    for post in posts:
        likes = LikedScreenplays.query.filter(LikedScreenplays.scriptid == post.scriptid, LikedScreenplays.rating >= 4.0)
        if likes.count() >= 10 and ScriptInFeatured(post.scriptid) == False: 
            newfeatured = FeaturedScripts(scriptid = post.scriptid, dequeuedatetime = datetime.now()+timedelta(hours=hour))
            db.session.add(newfeatured)
            db.session.commit()
            hour += 4
    for num in range(1,7): 
        script = FeaturedScripts.query.filter_by(featuredid = num).first()
        queue[num-1] = script

def GiveRecommendations(writerid): # Returns a list of 3 screenplay recommendations for a screenwriter user based on the genres the user likes
    UsersLikedPosts = LikedScreenplays.query.filter(LikedScreenplays.rating > 3.5).all()
    postids = [] 
    for post in UsersLikedPosts:
        if post.writerid == writerid:
            postids.append(post.scriptid) 
    if len(postids) == 0: 
        recs = None
        return recs
    
    else:
        LikedPostsGenreIDs = [] 
        for i in range(len(postids)):
            genreinfo = ScriptHas.query.filter(ScriptHas.scriptid == postids[i])
            for genre in genreinfo:
                 LikedPostsGenreIDs.append(genre.genreid) 

        GenreList = []
        for i in range(len(LikedPostsGenreIDs)):
            genre2 = Genres.query.filter(Genres.genreid ==  LikedPostsGenreIDs[i])
            for genre in genre2:
                GenreList.append(genre.genreid) 
        if (list(set(GenreList)) == GenreList and len(list(set(GenreList))) > 1) or len(GenreList) == 0:
            recs = None
            return recs
        else:
            favgenreid = max(set(GenreList), key = GenreList.count) 
            
        ScriptsofFavGenre = ScriptHas.query.filter(ScriptHas.genreid == favgenreid)
        ScriptShortlist = []
        for script in ScriptsofFavGenre:
            ScriptShortlist.append(script.scriptid) 
        
        LikedScriptIDs = [script.scriptid for script in LikedScreenplays.query.all()]
        recs = []
        for id in ScriptShortlist:
            if (id not in LikedScriptIDs): 
                script = Screenplays.query.filter(Screenplays.scriptid == id).first()
                if script.writer.user.id != current_user.id:
                    recs.append(script)
        return recs