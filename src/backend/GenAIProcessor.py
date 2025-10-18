from models import Destination

from langchain_community.chat_models import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Optional
import os
from google.cloud import vision
import base64
from PIL import Image
import io
import re
from dotenv import load_dotenv
load_dotenv()


class GenAIProcessor:
    def __init__(self, openai_api_key: str):
        """
        Initialize the GenAI processor with OpenAI API key.
        
        Args:
            openai_api_key (str): OpenAI API key for LLM access
        """
        # self.llm = ChatOpenAI(
        #     model_name="gpt-4-turbo-preview",
        #     temperature=0,
        #     openai_api_key=openai_api_key
        # )

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro",
            google_api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0
        )
        
        # Initialize Google Vision client
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        self.vision_client = vision.ImageAnnotatorClient()

    def _parse_destination_response(self, response, reelID:int) -> List[Destination]:
        """
        Parse LLM response into Destination objects.
        
        Args:
            response: The LLM response object
            
        Returns:
            List[Destination]: List of parsed destinations
        """
        destinations = []
        if response and response.content:
            # Split the response by the delimiter '*'
            parts = response.content.split('*')
            
            for part in parts:
                if not part.strip():
                    continue
                    
                # Extract destination name, description and confidence using regex
                dest_match = re.search(r'-Destination:\s*(.*?)(?=\s*-Description:|$)', part)
                desc_match = re.search(r'-Description:\s*(.*?)(?=\s*-Confidence:|$)', part)
                conf_match = re.search(r'-Confidence:\s*([\d.]+)', part)
                
                if dest_match:
                    name = dest_match.group(1).strip()
                    description = desc_match.group(1).strip() if desc_match else None
                    confidence = float(conf_match.group(1)) if conf_match else 1.0
                    
                    destination = Destination(
                        reel_id = reelID,
                        name=name,
                        description=description,
                        confidence=confidence
                    )
                    destinations.append(destination)
        
        return destinations

    def process_transcript(self, transcript: str, reelID) -> List[Destination]:
        """
        Process the audio transcript to identify travel destinations.
        
        Args:
            transcript (str): The transcribed audio text
            
        Returns:
            List[Destination]: List of identified destinations
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a travel destination analyzer. Your task is to:
            1. Determine if the given text is relevant to travel destinations
            2. If relevant, extract all mentioned destinations and places
            3. For each destination, provide a brief description if available
            4. Assign a confidence score (0-1) based on how clearly the destination is mentioned
            5. Correct any spelling errors and standardize capitalization based on context
               - Properly capitalize place names (e.g., "bali" → "Bali")
               - Fix common OCR errors (e.g., "ubud" → "Ubud")
               - Standardize location names to their official spelling
            
            Format your response as a list of destinations with their descriptions and confidence scores.
            Use the following format:
            * -Destination: destination name -Description: description -Confidence: confidence score * -Destination: destination name -Description: description-Confidence: confidence score; """),
            ("user", "{transcript}")
        ])
        
        chain = prompt | self.llm
        response = chain.invoke({"transcript": transcript})
        
        return self._parse_destination_response(response, reelID)

    def process_ocr_text(self, ocr_texts: List[str], reelID) -> List[Destination]:
        """
        Process OCR text to identify travel destinations.
        
        Args:
            ocr_texts (List[str]): List of text extracted from video frames
            
        Returns:
            List[Destination]: List of identified destinations
        """
        combined_text = "\n".join(ocr_texts)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a travel destination analyzer. Your task is to:
            1. Analyze the given text extracted from video frames
            2. Identify any travel destinations, landmarks, or places mentioned
            3. For each destination, provide a brief description if available
            4. Assign a confidence score (0-1) based on how clearly the destination is mentioned
            5. Correct any spelling errors and standardize capitalization based on context
               - Properly capitalize place names (e.g., "bali" → "Bali")
               - Fix common OCR errors (e.g., "ubud" → "Ubud")
               - Standardize location names to their official spelling
               - Handle currency and number formatting consistently
            
            Format your response as a list of destinations with their descriptions and confidence scores. 
            If the video only mentiones one locaion, provide the name of the location and a confidence score of 1
            Use the following format:
            * -Destination: destination name -Description: description -Confidence: confidence score * -Destination: destination name -Description: description-Confidence: confidence score; """),
            ("user", "{text}")
        ])
        
        chain = prompt | self.llm
        response = chain.invoke({"text": combined_text})
        
        destinations =  self._parse_destination_response(response, reelID)

        return destinations

    ##TODO- update this
    def process_image_frames(self, frame_paths: List[str]) -> List[Destination]:
        """
        Process image frames to identify travel destinations using Google Vision API.
        
        Args:
            frame_paths (List[str]): List of paths to image frames
            
        Returns:
            List[Destination]: List of identified destinations
        """
        destinations = []
        
        for frame_path in frame_paths:
            with open(frame_path, 'rb') as image_file:
                content = image_file.read()
            
            image = vision.Image(content=content)
            
            # Perform landmark detection
            response = self.vision_client.landmark_detection(image=image)
            landmarks = response.landmark_annotations
            
            for landmark in landmarks:
                destination = Destination(
                    name=landmark.description,
                    description=f"Detected landmark with {landmark.score:.2f} confidence",
                    confidence=landmark.score
                )
                destinations.append(destination)
        
        return destinations
