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
  return (
    <>
      {/* Profile Settings Modal */}
      {showProfileModal && (
        <ProfileSettingsModal
          isOpen={showProfileModal}
          onClose={() => setShowProfileModal(false)}
          user={user}
          analyticsData={analyticsData}
          token={token}
        />
      )}
      
      {/* Preferences Modal */}
      {showPreferencesModal && (
        <PreferencesModal
          isOpen={showPreferencesModal}
          onClose={() => setShowPreferencesModal(false)}
          audioNarrativeEnabled={audioNarrativeEnabled}
        />
      )}
      
      {/* Help & Support Modal */}
      {showHelpModal && (
        <HelpSupportModal
          isOpen={showHelpModal}
          onClose={() => setShowHelpModal(false)}
          onOpenFeedback={handleOpenFeedback}
        />
      )}
      
      {/* Send Feedback Modal */}
      {showFeedbackModal && (
        <FeedbackModal
          isOpen={showFeedbackModal}
          onClose={() => setShowFeedbackModal(false)}
          token={token}
        />
      )}
    </>
  );
};

export default AccountModals;