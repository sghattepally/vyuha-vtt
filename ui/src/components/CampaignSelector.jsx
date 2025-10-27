// ui/src/components/CampaignSelector.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

function CampaignSelector({ sessionId, sessionData, onCampaignSelected }) {
  const [campaigns, setCampaigns] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // Fetch available campaigns
    axios.get('http://localhost:8000/campaigns?published_only=true')
      .then(response => setCampaigns(response.data))
      .catch(error => console.error("Failed to fetch campaigns", error));
  }, []);

  const handleSelectCampaign = async (campaignId) => {
    setIsLoading(true);
    try {
      await axios.post(
        `http://localhost:8000/sessions/${sessionId}/select_campaign`,
        null,
        { params: { campaign_id: campaignId } }
      );
      if (onCampaignSelected) onCampaignSelected(campaignId);
    } catch (error) {
      console.error("Failed to select campaign", error);
    } finally {
      setIsLoading(false);
    }
  };

  // If campaign already selected, show it
  if (sessionData?.campaign_id) {
    const selectedCampaign = campaigns.find(c => c.id === sessionData.campaign_id);
    return (
      <div className="campaign-selected">
        <h3>Selected Campaign</h3>
        <div className="campaign-card selected">
          <h4>{selectedCampaign?.name || "Loading..."}</h4>
          <p>{selectedCampaign?.description}</p>
          {selectedCampaign && (
            <div className="campaign-meta">
              <span>Level {selectedCampaign.recommended_level}</span>
              <span>{selectedCampaign.recommended_party_size} players</span>
              <span>~{selectedCampaign.estimated_duration_minutes} min</span>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="campaign-selector">
      <h3>Select a Campaign</h3>
      {campaigns.length === 0 ? (
        <p className="placeholder-text">No campaigns available. Create one first!</p>
      ) : (
        <div className="campaign-list">
          {campaigns.map(campaign => (
            <div key={campaign.id} className="campaign-card">
              <h4>{campaign.name}</h4>
              <p>{campaign.description}</p>
              <div className="campaign-meta">
                <span>📊 Level {campaign.recommended_level}</span>
                <span>👥 {campaign.recommended_party_size} players</span>
                <span>⏱️ ~{campaign.estimated_duration_minutes} min</span>
              </div>
              <button 
                onClick={() => handleSelectCampaign(campaign.id)}
                disabled={isLoading}
                className="select-campaign-button"
              >
                {isLoading ? 'Selecting...' : 'Select Campaign'}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default CampaignSelector;