# src/Core/Tools/social_data.py
# TODO : REFACTOR INTO THE APPROPRIATE TWITTER_DATA SUB-DIRECTORY SO THAT WE CAN SPLIT OUT MODELS AND LOGIC

import os
import re
import httpx
from typing import Optional, List, Dict, Annotated
from pydantic import BaseModel, Field
from pydantic_ai.tools import Tool 

# --- Pydantic Models (Optimized for API Response) ---
# (Keep the Pydantic models exactly as before)
class TweetUser(BaseModel):
    """Represents a Twitter user, optimized for SocialData API."""
    id: Annotated[int, Field(description="The unique numerical ID of the user.")]
    id_str: Annotated[str, Field(description="String representation of the user ID.")]
    name: Annotated[str, Field(description="The user's display name.")]
    screen_name: Annotated[str, Field(description="The user's Twitter handle (screen name).")]
    location: Annotated[Optional[str], Field(description="The user's location, if provided.")]
    url: Annotated[Optional[str], Field(description="The URL associated with the user's profile.")]
    description: Annotated[Optional[str], Field(description="The user's profile description.")]
    protected: Annotated[bool, Field(description="Whether the user's account is protected.")]
    verified: Annotated[bool, Field(description="Whether the user's account is verified.")]
    followers_count: Annotated[int, Field(description="The number of followers.")]
    friends_count: Annotated[int, Field(description="The number of accounts this user is following.")]
    listed_count: Annotated[int, Field(description="The number of public lists the user is a member of.")]
    favourites_count: Annotated[int, Field(description="The number of tweets this user has liked.")]
    statuses_count: Annotated[int, Field(description="The number of tweets (including retweets) posted by this user.")]
    created_at: Annotated[str, Field(description="The UTC datetime string that the user account was created.")]
    profile_banner_url: Annotated[Optional[str], Field(description="URL of the profile banner image.")]
    profile_image_url_https: Annotated[str, Field(description="URL of the profile image (HTTPS).")]
    can_dm: Annotated[bool, Field(description="If the user can receive DMs.")]

class TweetEntities(BaseModel):
    """Represents entities within a tweet (hashtags, URLs, etc.)."""
    hashtags: Annotated[List[Any], Field(default_factory=list, description="List of hashtags.")]
    symbols: Annotated[List[Any], Field(default_factory=list, description="List of stock symbols.")]
    timestamps: Annotated[List[Any], Field(default_factory=list, description="List of timestamps.")]
    urls: Annotated[List[Any], Field(default_factory=list, description="List of URLs.")]
    user_mentions: Annotated[List[Any], Field(default_factory=list, description="List of user mentions.")]
    media: Annotated[Optional[List[Any]], Field(default_factory=list, description="List of media, added from twitter search sample")]

class Tweet(BaseModel):
    """Represents a tweet, optimized for the SocialData API."""
    tweet_created_at: Annotated[str, Field(description="The creation timestamp of the tweet in ISO 8601 format.")]
    id: Annotated[int, Field(description="The unique numerical ID of the tweet.")]
    id_str: Annotated[str, Field(description="String representation of the tweet ID.")]
    conversation_id_str: Annotated[str, Field(description="String ID of the conversation the tweet belongs to.")]
    text: Annotated[Optional[str], Field(description="The text content of the tweet (usually null for full_text).")]
    full_text: Annotated[str, Field(description="The full text content of the tweet.")]
    source: Annotated[str, Field(description="Source client the tweet was posted from.")]
    truncated: Annotated[bool, Field(description="Whether the tweet was truncated.")]
    in_reply_to_status_id: Annotated[Optional[int], Field(description="ID of the tweet this is in reply to.")]
    in_reply_to_status_id_str: Annotated[Optional[str], Field(description="String ID of the tweet this is in reply to.")]
    in_reply_to_user_id: Annotated[Optional[int], Field(description="ID of the user this is in reply to.")]
    in_reply_to_user_id_str: Annotated[Optional[str], Field(description="String ID of the user this is in reply to.")]
    in_reply_to_screen_name: Annotated[Optional[str], Field(description="Screen name of the user this is in reply to.")]
    user: Annotated[TweetUser, Field(description="The author of the tweet.")]
    quoted_status_id: Annotated[Optional[int], Field(description="ID of the quoted tweet.")]
    quoted_status_id_str: Annotated[Optional[str], Field(description="String ID of the quoted tweet.")]
    is_quote_status: Annotated[bool, Field(description="Whether this is a quote tweet.")]
    quoted_status:  Annotated[Optional[dict], Field(description="The full quoted status.")]
    retweeted_status:  Annotated[Optional[dict], Field(description="The retweet status.")]
    quote_count: Annotated[Optional[int], Field(description="The number of times the tweet has been quoted.")]
    reply_count: Annotated[Optional[int], Field(description="The number of replies the tweet has received.")]
    retweet_count: Annotated[Optional[int], Field(description="The number of times the tweet has been retweeted.")]
    favorite_count: Annotated[Optional[int], Field(description="The number of times the tweet has been favorited.")]
    views_count: Annotated[Optional[int], Field(description="The number of views the tweet has.")]
    bookmark_count: Annotated[Optional[int], Field(description="The number of times the tweet has been bookmarked.")]
    lang: Annotated[Optional[str], Field(description="The BCP 47 language identifier of the tweet.")]
    entities: Annotated[TweetEntities, Field(description="Entities within the tweet.")]
    is_pinned: Annotated[bool, Field(description="Whether the tweet is a pinned tweet")]

class ExtractedToken(BaseModel):
    token: Annotated[str, Field(description="The crypto token symbol mentioned in the tweet")]

class SocialDataToolOutput(BaseModel):
    original_tweet: Annotated[Tweet, Field(description="The original tweet from MegaWhaleTrades.")]
    extracted_token: Annotated[ExtractedToken, Field(description="The extracted token from the original tweet.")]

class LatestTweetInput(BaseModel):
    username: Annotated[str, Field("MegaWhaleTrades", description="The Twitter username to fetch. Defaults to MegaWhaleTrades.")]

class TwitterSearchInput(BaseModel):
    query: Annotated[str, Field(description="The term to search for on Twitter.")]
    max_results: Annotated[int, Field(20, description="Max number of tweets to return. Defaults to 20, max is 20.")] = 20

class TwitterSearchOutput(BaseModel):
    tweets: Annotated[List[Tweet], Field(description="The list of tweets returned by the API.")]
    next_cursor: Annotated[Optional[str], Field(description="The cursor for the next page of results, if available.")] = None


@tool
async def get_latest_tweet(username: str = "MegaWhaleTrades") -> SocialDataToolOutput:
    """
    Fetches the latest tweet from a specified Twitter user (defaults to MegaWhaleTrades).
    """
    api_key = os.getenv("SOCIALDATA_API_KEY")
    if not api_key:
        raise ValueError("SOCIALDATA_API_KEY environment variable not set.")

    url = f"https://api.socialdata.tools/twitter/user/{username}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            user = TweetUser(**data['user'])
            tweet = Tweet(**data, user=user)
            match = re.search(r"[$#]([A-Z0-9]{1,5})", tweet.full_text)
            if not match:
                raise ValueError("Unable to extract the token.")

            extracted_token = ExtractedToken(token=match.group(1))
            return SocialDataToolOutput(original_tweet=tweet, extracted_token=extracted_token)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 402:
                raise ValueError("Insufficient SocialData API credits.")
            elif e.response.status_code == 404:
                raise ValueError(f"User {username} not found.")
            raise ValueError(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise ValueError(f"An unexpected error occurred: {str(e)}")

@tool
async def get_tweets_from_search(query: str, max_results: int = 20) -> TwitterSearchOutput:
    """
    Fetches tweets matching a query from Twitter.
    """
    api_key = os.getenv("SOCIALDATA_API_KEY")
    if not api_key:
        raise ValueError("SOCIALDATA_API_KEY environment variable not set.")

    url = "https://api.socialdata.tools/twitter/search"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }
    params = {
        "query": query,
        "type": "Latest",
        "max_results": max_results,
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            tweets = [Tweet(**tweet_data) for tweet_data in data.get('tweets', [])]
            return TwitterSearchOutput(tweets=tweets, next_cursor=data.get("next_cursor"))


        except httpx.HTTPStatusError as e:
            if e.response.status_code == 402:
                raise ValueError("Insufficient SocialData API credits.")
            raise ValueError(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise ValueError(f"An unexpected error occurred: {str(e)}")