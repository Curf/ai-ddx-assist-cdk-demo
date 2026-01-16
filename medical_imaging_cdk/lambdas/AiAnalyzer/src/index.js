const { LiteLLM } = require('litellm');
const { Langfuse } = require('langfuse');
const AWS = require('aws-sdk');
const s3 = new AWS.S3();
const dynamoDB = new AWS.DynamoDB.DocumentClient();

// Initialize Langfuse for prompt tracking and management
const langfuse = new Langfuse({
  secretKey: process.env.LANGFUSE_SECRET_KEY,
  publicKey: process.env.LANGFUSE_PUBLIC_KEY,
  baseUrl: process.env.LANGFUSE_BASE_URL || 'https://cloud.langfuse.com'
});

// Initialize LiteLLM for model provider access
const litellm = new LiteLLM({
  apiKey: process.env.OPENAI_API_KEY,
  defaultProvider: 'openai'
});

/**
 * Analyzes a medical image using AI models and stores the results
 * @param {Object} event - Event data from Step Functions or S3
 * @param {Object} context - AWS Lambda context
 * @returns {Object} Analysis results including findings and confidence scores
 */
exports.handler = async (event, context) => {
  console.log('Received event:', JSON.stringify(event, null, 2));
  
  try {
    // Extract image information from the event
    let imageId, s3Key, patientId, clinicId, imageType;
    
    // Handle event coming from Step Functions
    if (event.processingResult && event.processingResult.Payload) {
      const payload = event.processingResult.Payload;
      imageId = payload.imageId;
      s3Key = payload.s3Key;
      patientId = payload.patientId;
      clinicId = payload.clinicId;
      imageType = payload.imageType;
    } 
    // Handle event coming directly from S3
    else if (event.Records && event.Records[0] && event.Records[0].s3) {
      s3Key = decodeURIComponent(event.Records[0].s3.object.key);
      
      // Parse metadata from s3Key: uploads/clinicId/patientId/imageId.jpg
      const keyParts = s3Key.split('/');
      clinicId = keyParts[1];
      patientId = keyParts[2];
      imageId = keyParts[3].split('.')[0];
      imageType = s3Key.split('.').pop().toLowerCase();
    } else {
      throw new Error('Invalid event structure');
    }
    
    console.log(`Processing image ${imageId} for patient ${patientId}`);
    
    // Create a trace in Langfuse to track the AI analysis process
    const trace = langfuse.trace({
      name: 'medical_image_analysis',
      userId: patientId,
      metadata: {
        imageId,
        clinicId,
        imageType
      }
    });
    
    // Download image from S3
    const s3Object = await s3.getObject({
      Bucket: 'medical-imaging-files-dev',
      Key: s3Key
    }).promise();
    
    // Convert image to base64 for AI model consumption
    const imageBase64 = s3Object.Body.toString('base64');
    
    // First step: Get initial assessment using a vision model
    const visionSpan = trace.span({ name: 'vision_analysis' });
    const visionResponse = await litellm.completion({
      model: 'gpt-4-vision',
      messages: [
        {
          role: 'system',
          content: 'You are a medical imaging expert. Analyze the provided image and identify potential abnormalities or findings.'
        },
        {
          role: 'user',
          content: [
            { type: 'text', text: `Please analyze this ${imageType} medical image and describe what you see:` },
            { type: 'image_url', image_url: { url: `data:image/${imageType};base64,${imageBase64}` } }
          ]
        }
      ],
      max_tokens: 500
    });
    
    const initialAnalysis = visionResponse.choices[0].message.content;
    visionSpan.end();
    
    // Second step: Get detailed diagnosis possibilities using LLM
    const diagnosisSpan = trace.span({ name: 'diagnosis_generation' });
    const diagnosisResponse = await litellm.completion({
      model: 'gpt-4-turbo',
      messages: [
        {
          role: 'system',
          content: 'You are a medical diagnostic assistant that provides potential diagnoses based on imaging findings.'
        },
        {
          role: 'user',
          content: `Based on the following imaging findings, provide a ranked list of 3-5 potential diagnoses with confidence levels (as percentages). Include ICD-10 codes if applicable.\n\nImage type: ${imageType}\nFindings: ${initialAnalysis}`
        }
      ],
      max_tokens: 1000
    });
    
    const diagnosisText = diagnosisResponse.choices[0].message.content;
    diagnosisSpan.end();
    
    // Extract highest confidence diagnosis
    const confidenceRegex = /(\d{1,3})%/g;
    const confidences = diagnosisText.match(confidenceRegex);
    let highestConfidence = 0;
    
    if (confidences && confidences.length > 0) {
      highestConfidence = Math.max(...confidences.map(c => parseInt(c)));
    }
    
    // Store the analysis results in DynamoDB
    const timestamp = Math.floor(Date.now() / 1000);
    const analysisItem = {
      imageId: imageId,
      clinicId: clinicId,
      patientId: patientId,
      findings: diagnosisText,
      initialAnalysis: initialAnalysis,
      confidence: highestConfidence,
      status: 'ANALYZED',
      timestamp: timestamp,
      traceId: trace.id
    };
    
    await dynamoDB.put({
      TableName: 'AnalysisResults',
      Item: analysisItem
    }).promise();
    
    trace.end();
    
    // Return the analysis results
    const result = {
      imageId,
      patientId,
      clinicId,
      findings: diagnosisText,
      confidence: highestConfidence,
      status: 'SUCCESS'
    };
    
    console.log('Analysis completed:', JSON.stringify(result, null, 2));
    return result;
    
  } catch (error) {
    console.error('Error processing image:', error);
    
    return {
      status: 'ERROR',
      error: error.message,
      imageId: event.imageId || 'UNKNOWN'
    };
  }
};
