#!/usr/bin/env python3

from flask import request, session, jsonify
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe

class Signup(Resource):
    def post(self):
        json = request.get_json()
        username = json.get('username')
        password = json.get('password')
        if not username or not password:
            return {"error": "Username and password are required."}, 422
        if User.query.filter_by(username=username).first():
            return {"error": "Username already exists."}, 422
        user = User(
            username=username,
            image_url = json['image_url'],
            bio = json['bio'],
        )
        user.password_hash = password
        session['user_id'] = user.id
        
        db.session.add(user)
        db.session.commit()
        return user.to_dict(), 201

class CheckSession(Resource):
    def get(self):
        user = User.query.filter_by(id=session.get('user_id')).first()
        if user:
            return user.to_dict()
        else:
            return {}, 401

class Login(Resource):
    def post(self):
        username = request.get_json()['username']
        user = User.query.filter_by(username=username).first()
        password = request.get_json()['password']
        if not user:
            return {"error": "invalid username and password."}, 401
        elif user.authenticate(password):
            session['user_id'] = user.id
            return user.to_dict(), 200
       
            

class Logout(Resource):
    def delete(self):
        if 'user_id' not in session or session['user_id'] is None:
            return {"error": "Unauthorized"}, 401
        session.pop('user_id', None)
        return {}, 204

class RecipeIndex(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return {"error": "Unauthorized"}, 401
        recipes = Recipe.query.filter_by(user_id=user_id).all()
        recipes_to_dict = []
        for recipe in recipes:
            # Convert the recipe to a dictionary
            recipe_dict = {
                'id': recipe.id,
                'title': recipe.title,
                'instructions': recipe.instructions,
                'minutes_to_complete': recipe.minutes_to_complete
            }

            # Fetch the user data for the recipe
            user = User.query.get(recipe.user_id)
            if user:
                # Add user data to the recipe dictionary
                recipe_dict['user'] = {
                    'id': user.id,
                    'username': user.username,
                    'image_url': user.image_url,
                    'bio': user.bio
                }
            
            recipes_to_dict.append(recipe_dict)
        return recipes_to_dict, 200
    
    def post(self):
        user_id = session.get('user_id')
        if not user_id:
            return {"error": "Unauthorized"}, 401
        json = request.get_json()
        title = json.get('title')
        instructions = json.get('instructions')
        minutes_to_complete = json.get('minutes_to_complete')

        if not title or not instructions or not minutes_to_complete:
            return {"error": "Title, instructions, and minutes to complete are required."}, 422
        if len(instructions) < 50:
            return {"error": "Instructions must be at least 50 characters long"}, 422
        new_recipe = Recipe(
            title=title,
            instructions=instructions,
            minutes_to_complete=minutes_to_complete,
            user_id=user_id
        )
        db.session.add(new_recipe)
        db.session.commit()

        user = User.query.filter_by(id=user_id).first()
        recipe_response = {
            'title': new_recipe.title,
            'instructions': new_recipe.instructions,
            'minutes_to_complete': new_recipe.minutes_to_complete,
            'user': {
                'id': user.id,
                'username': user.username,
                'image_url': user.image_url,
                'bio': user.bio
            }
        }
        return recipe_response, 201




api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)