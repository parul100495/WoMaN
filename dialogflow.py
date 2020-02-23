try:
    import urllib
    import json
    import os
    from flask import (Flask, request, make_response)
    from flask import jsonify
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    from nltk.stem import WordNetLemmatizer
    from rake_nltk import Rake
    from collections import OrderedDict
    import numpy as np
    import spacy
    from spacy.lang.en.stop_words import STOP_WORDS
    from flask_cors import CORS

    nlp = spacy.load('en_core_web_sm')
except Exception as e:
    print("Some modules are missing {}".format(e))

app = Flask(__name__)
CORS(app)

# ------ Firebase ----------
import pyrebase

config = {
  "apiKey": "your-api-key",
  "authDomain": "your-auth-domain.firebaseapp.com",
  "databaseURL": "https://your-database-url.firebaseio.com",
  "storageBucket": "your-storage-bucket-name.appspot.com",
  "serviceAccount": "serviceacc.json"
}

firebase = pyrebase.initialize_app(config)

# Get a reference to the auth service
auth = firebase.auth()

email = 'test@gmail.com'
password =  'test'

#auth.create_user_with_email_and_password(email, password)

# Log the user in
user = auth.sign_in_with_email_and_password(email, password)

# Get a reference to the database service
db = firebase.database()

# ------ Constants --------
FILENAME = 'filename'
TAGNAME = 'tagname'
AND = ' and '

# ------ Gmail cred --------
import smtplib

gmail_user = 'test@gmail.com'
gmail_password = 'test'

sent_from = gmail_user

# ------ ML related ----------
#lemmatizer = WordNetLemmatizer()
#stop_words = set(stopwords.words('english'))
#r = Rake(min_length=1, max_length=2)

class TextRank4Keyword():
    """Extract keywords from text"""
    
    def __init__(self):
        self.d = 0.85 # damping coefficient, usually is .85
        self.min_diff = 1e-5 # convergence threshold
        self.steps = 10 # iteration steps
        self.node_weight = None # save keywords and its weight

    
    def set_stopwords(self, stopwords):  
        """Set stop words"""
        for word in STOP_WORDS.union(set(stopwords)):
            lexeme = nlp.vocab[word]
            lexeme.is_stop = True
    
    def sentence_segment(self, doc, candidate_pos, lower):
        """Store those words only in cadidate_pos"""
        sentences = []
        for sent in doc.sents:
            selected_words = []
            for token in sent:
                # Store words only with cadidate POS tag
                if token.pos_ in candidate_pos and token.is_stop is False:
                    if lower is True:
                        selected_words.append(token.text.lower())
                    else:
                        selected_words.append(token.text)
            sentences.append(selected_words)
        return sentences
        
    def get_vocab(self, sentences):
        """Get all tokens"""
        vocab = OrderedDict()
        i = 0
        for sentence in sentences:
            for word in sentence:
                if word not in vocab:
                    vocab[word] = i
                    i += 1
        return vocab
    
    def get_token_pairs(self, window_size, sentences):
        """Build token_pairs from windows in sentences"""
        token_pairs = list()
        for sentence in sentences:
            for i, word in enumerate(sentence):
                for j in range(i+1, i+window_size):
                    if j >= len(sentence):
                        break
                    pair = (word, sentence[j])
                    if pair not in token_pairs:
                        token_pairs.append(pair)
        return token_pairs
        
    def symmetrize(self, a):
        return a + a.T - np.diag(a.diagonal())
    
    def get_matrix(self, vocab, token_pairs):
        """Get normalized matrix"""
        # Build matrix
        vocab_size = len(vocab)
        g = np.zeros((vocab_size, vocab_size), dtype='float')
        for word1, word2 in token_pairs:
            i, j = vocab[word1], vocab[word2]
            g[i][j] = 1
            
        # Get Symmeric matrix
        g = self.symmetrize(g)
        
        # Normalize matrix by column
        norm = np.sum(g, axis=0)
        g_norm = np.divide(g, norm, where=norm!=0) # this is ignore the 0 element in norm
        
        return g_norm

    
    def get_keywords(self, number=10):
        """Returns top number keywords"""
        node_weight = OrderedDict(sorted(self.node_weight.items(), key=lambda t: t[1], reverse=True))
        tags = []
        for i, (key, value) in enumerate(node_weight.items()):
            tags.append(key)
            if i > number:
                break
        return tags
        
        
    def analyze(self, text, 
                candidate_pos=['NOUN', 'PROPN'], 
                window_size=4, lower=False, stopwords=list()):
        """Main function to analyze text"""
        
        # Set stop words
        self.set_stopwords(stopwords)
        
        # Pare text by spaCy
        doc = nlp(text)
        
        # Filter sentences
        sentences = self.sentence_segment(doc, candidate_pos, lower) # list of list of words
        
        # Build vocabulary
        vocab = self.get_vocab(sentences)
        
        # Get token_pairs from windows
        token_pairs = self.get_token_pairs(window_size, sentences)
        
        # Get normalized matrix
        g = self.get_matrix(vocab, token_pairs)
        
        # Initionlization for weight(pagerank value)
        pr = np.array([1] * len(vocab))
        
        # Iteration
        previous_pr = 0
        for epoch in range(self.steps):
            pr = (1-self.d) + self.d * np.dot(g, pr)
            if abs(previous_pr - sum(pr))  < self.min_diff:
                break
            else:
                previous_pr = sum(pr)

        # Get weight for each node
        node_weight = dict()
        for word, index in vocab.items():
            node_weight[word] = pr[index]
        
        self.node_weight = node_weight

# ------ Webhook -------------
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        req = request.get_json(silent=True,force=True)
        res = processRequest(req)
        return res

def processRequest(req):
    query_response = req['queryResult']
    print(query_response)
    intent = query_response.get('intent', None)
    task = intent.get('displayName', None)
    if task == 'SaveContact':
        print('---------Adding a new contact---------')
        parameters = query_response.get('parameters', None)
        res = save_contact(parameters.get('name', None), parameters.get('email', None))

    elif task == 'RetrieveContact':
        print('---------Retrieving an existing contact---------')
        parameters = query_response.get('parameters', None)
        res = retrieve_contact(parameters.get('name', None))

    elif task == 'TakeNotes':
        print('---------Adding a new note---------')
        parameters = query_response.get('parameters', None)
        res = save_note(parameters.get('filename', None), parameters.get('text', None))

    elif task == 'RetrieveNotesByFilename':
        print('---------Retrieving an existing note by filename---------')
        parameters = query_response.get('parameters', None)
        res = retrieve_note_by_filename(parameters.get('filename', None))

    elif task == 'RetrieveNotesByTag':
        print('---------Retrieving an existing note by tag---------')
        parameters = query_response.get('parameters', None)
        res = retrieve_note_by_tag(parameters.get('tag', None))

    elif task == 'SendEmailByFilename':
        print('---------Sending an email by filename---------')
        parameters = query_response.get('parameters', None)
        output_context = query_response.get('outputContexts', None)
        filename = None
        for i in output_context:
            p = i['parameters']
            if 'filename' in p:
                filename = p['filename']
                break
        if filename:
            res = send_email(filename, parameters.get('name', None), FILENAME)
        else:
            res = _undefined_file_or_tag_email(parameters.get('name', None))

    elif task == 'SendEmailByTag':
        print('---------Sending an email by tag---------')
        parameters = query_response.get('parameters', None)
        output_context = query_response.get('outputContexts', None)
        tag = None
        for i in output_context:
            p = i['parameters']
            if 'tag' in p:
                tag = p['tag']
                break
        if tag:
            res = send_email(tag, parameters.get('name', None), TAGNAME)
        else:
            res = _undefined_file_or_tag_email(parameters.get('name', None))

    elif task == 'RetrieveUIData':
        print('---------Retrieving data for UI---------')
        parameters = query_response.get('parameters', None)
        res = retrieve_data_for_ui(parameters.get('tag', None))
    else:
        speech = 'Task not added yet... Try later'
        res = processResult(speech)
    return res

def processResult(out_put):
    reply = {
        "fulfillmentText": out_put,
    }
    return jsonify(reply)

def save_contact(name, email):
    try:
        # save to db
        key_value_data = {"email": email}
        db.child("contact").child(name).set(key_value_data)
        speech = 'Sucessfully saved the new contact {} with email {}'.format(name, email)
    except Exception as e:
        speech = 'Exception occurred {}'.format(e)
    return processResult(speech)

def retrieve_contact(name):
    try:
        email = _contact_retrieve(name)
        speech = 'Sucessfully retrieved an existing contact {} with email {}'.format(name, email)
    except Exception as e:
        speech = 'Exception occurred {}'.format(e)
    return processResult(speech)

# ------ For internal usage ------
def _contact_retrieve(name):
    email = None
    try:
        # get from db
        users = db.child("contact").get().val()
        if users:
            user = users[name]
            if user:
                email = user["email"]
    except Exception as e:
        raise Exception(e)
    return email

def save_note(filename, text):
    try:
        # save to db
        db.child("data").child("document").child(filename).set(text)

        tags = _get_tags(text)
        for t in tags:
            # check if tag exists in db
            t_docs = _get_tag_value(t)
            if t_docs:
                # add filename to list
                t_docs = t_docs + ',' + filename
                # save to db
                db.child("data").child("tags").child(t).set(t_docs)
            else:
                # add new tag
                t_docs = filename
                # save to db
                db.child("data").child("tags").child(t).set(t_docs)

        speech = 'Sucessfully saved the note with filename {}'.format(filename)
    except Exception as e:
        speech = 'Exception occurred {}'.format(e) 
    return processResult(speech)

# ------ For internal usage ------
def _get_tags(text):
    tags = []
    try:
        tr4w = TextRank4Keyword()
        tr4w.analyze(text, candidate_pos = ['NOUN', 'PROPN'], window_size=4, lower=True)
        tags = tr4w.get_keywords(5)
    except Exception as e:
        raise Exception(e)
    return tags

# ------ For internal usage ------
def _get_tag_value(t):
    value = None
    try:
        # get from db
        tags = db.child("data").child("tags").get().val()
        if tags and t in tags.keys():
            value = tags[t]
    except Exception as e:
        raise Exception(e)
    return value

def retrieve_note_by_filename(filename):
    try:
        text = _note_retrieve(filename)
        speech = '{}'.format(text)
    except Exception as e:
        speech = 'Exception occurred {}'.format(e)
    return processResult(speech)

def retrieve_note_by_tag(tag):
    try:
        text = _note_retrieve_by_tag(tag)
        speech = '{}'.format(text)
    except Exception as e:
        speech = 'Exception occurred {}'.format(e)
    return processResult(speech)

# ------ For internal usage ------
def _note_retrieve_by_tag(tag):
    text = None
    try:
        filename = _fetch_last_filename(tag)
        text = _note_retrieve(filename)
    except Exception as e:
        raise Exception(e)
    return text

# ------ For internal usage ------
def _fetch_last_filename(tag):
    filename = None
    try:
        tag_list = tag.split(AND)
        filenames = _get_tag_value(tag_list[0])
        final_files = filenames.split(',')
        
        for t in tag_list:
            filenames = _get_tag_value(t)
            list_of_files = filenames.split(',')
            final_files = set(final_files).intersection(list_of_files)
        
        final_files = list(final_files)
        if final_files:
            filename = final_files[len(final_files) - 1]
    except Exception as e:
        raise Exception(e)
    return filename

# ------ For internal usage ------
def _note_retrieve(filename):
    text = None
    try:
        # get from db
        text = db.child("data").child("document").child(filename).get().val()
    except Exception as e:
        raise Exception(e)
    return text

def send_email(ret_name, name, ret_type):
    try:
        email = _contact_retrieve(name)
        if ret_type == FILENAME:
            text = _note_retrieve(ret_name)
            filename = ret_name
        elif ret_type == TAGNAME:
            text = _note_retrieve_by_tag(ret_name)
            filename = _fetch_last_filename(ret_name)
        else:
            return _undefined_file_or_tag_email(name)
        if email:
            to = [email]
            subject = "A new message from Parul's chatbot"
            body = text
            email_text = """\
From: {}
To: {}
Subject: {}
Hi,
{}
From,
Team Woman.
""".format(sent_from, ", ".join(to), subject, body)
            
            # send the email
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.ehlo()
            server.login(gmail_user, gmail_password)
            server.sendmail(sent_from, to, email_text)
            server.close()

            # save entry to db
            saved = _save_doc_to_name(filename, name)
            if saved:
                speech = 'Email sent to {}.'.format(name)
        else:
            speech = 'Contact is not configured. Try saving a new contact first.'
    except Exception as e:
        speech = 'Exception occurred: {}'.format(e)
    return processResult(speech)

def _save_doc_to_name(filename, name):
    saved = False
    try:
        # check if tag exists in db
        names = _get_names_by_doc(filename)
        if names:
            # add name to list
            names = names + ',' + name
            # save to db
            db.child("data").child("doctoname").child(filename).set(names)
        else:
            # add new filename
            names = name
            # save to db
            db.child("data").child("doctoname").child(filename).set(names)
        saved = True
    except Exception as e:
        raise Exception(e)
    return saved

def _get_names_by_doc(filename):
    value = None
    try:
        # get from db
        value = db.child("data").child("doctoname").child(filename).get().val()
    except Exception as e:
        raise Exception(e)
    return value

def _undefined_file_or_tag_email(name):
    speech = "Filename or tag name doesn't exist. No email sent to {}".format(name)
    return processResult(speech)

def retrieve_data_for_ui(tag):
    try:
        filenames = _get_tag_value(tag)
        list_files = filenames.split(',')
        d_files = {}
        print(list_files)
        for i in list_files:
            text = _note_retrieve(i)
            names = _get_names_by_doc(i)
            if names:
                list_names = names.split(',')
                d_files[i] = {"text": text, "names": list_names}
            else:
                d_files[i] = {"text": text}
        speech = {tag: d_files}
        print(speech)
    except Exception as e:
        speech = 'Exception occurred {}'.format(e)
        print(speech)
    return (json.dumps(speech), 200, {'content-type': 'application/json'})

if __name__ == "__main__":
    app.run() 

