import React from 'react';
import { ProfileSettingsModal, PreferencesModal, HelpSupportModal, FeedbackModal } from './AccountModals';

// This component renders all the modals needed for the account dropdown
const AccountModals = ({ 
  showProfileModal, 
  setShowProfileModal, 
  showPreferencesModal, 
  setShowPreferencesModal,
  showHelpModal,
  setShowHelpModal,
  showFeedbackModal,
  setShowFeedbackModal,
  user,
  analyticsData,
  token,
  audioNarrativeEnabled,
  handleOpenFeedback
}) => {
  console.log('🔍 AccountModals component rendered with props:', {
    showProfileModal,
    showPreferencesModal,
    showHelpModal,
    showFeedbackModal,
    user: user ? 'present' : 'missing',
    token: token ? 'present' : 'missing'
  });
  
  return (
    <>
      {/* Profile Settings Modal */}
      {showProfileModal && (
        <ProfileSettingsModal
          isOpen={showProfileModal}
          onClose={() => {
            console.log('🔍 Profile modal close handler called');
            setShowProfileModal(false);
          }}
          user={user}
          analyticsData={analyticsData}
          token={token}
        />
      )}
      
      {/* Preferences Modal */}
      {showPreferencesModal && (
        <PreferencesModal
          isOpen={showPreferencesModal}
          onClose={() => {
            console.log('🔍 Preferences modal close handler called');
            setShowPreferencesModal(false);
          }}
          audioNarrativeEnabled={audioNarrativeEnabled}
        />
      )}
      
      {/* Help & Support Modal */}
      {showHelpModal && (
        <HelpSupportModal
          isOpen={showHelpModal}
          onClose={() => {
            console.log('🔍 Help modal close handler called');
            setShowHelpModal(false);
          }}
          onOpenFeedback={handleOpenFeedback}
        />
      )}
      
      {/* Send Feedback Modal */}
      {showFeedbackModal && (
        <FeedbackModal
          isOpen={showFeedbackModal}
          onClose={() => {
            console.log('🔍 Feedback modal close handler called');
            setShowFeedbackModal(false);
          }}
          token={token}
        />
      )}
    </>
  );
};

export default AccountModals;