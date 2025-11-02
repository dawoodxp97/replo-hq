import { useState, useRef, useEffect } from 'react';
import { Button } from 'antd';
import { Github, Gitlab, Plug2, User } from 'lucide-react';
import Image from 'next/image';
import { toast } from 'sonner';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import { snakeToCamel } from '@/utils/common';
import { getAccountIcon } from '@/utils/customIcons';

import SaveSettingsChanges from './SaveSettingsChanges';
import ReploInput from '@/components/ui/input/Input';
import Loader from '@/components/ui/loader/Loader';
import Error from '@/components/ui/error/Error';

import {
  getUserProfileSettings,
  ProfileSettingsResponse,
  ProfileSettingsUpdate,
  updateUserProfileSettings,
} from '@/services/settingsService';
import { SettingsCard, SettingsContentWrapper } from '../layout/SettingsLayout';

type PIIDetailsState = {
  firstName: string;
  lastName: string;
  email: string;
  bio: string;
  location: string;
  website: string;
  profilePic: string;
  connectedAccounts: {
    id: number;
    name: string;
    icon: React.ReactNode;
    connected: boolean;
    username: string;
  }[];
};

const ProfileSettings = () => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const {
    data: profileSettingsData,
    isPending,
    isFetching,
    error: errorProfileSettings,
  } = useQuery<PIIDetailsState>({
    queryKey: ['profileSettings'],
    queryFn: async () => {
      const response = await getUserProfileSettings();
      const camelData = snakeToCamel<PIIDetailsState>(response);
      return camelData;
    },
    retry: false,
  });

  const updateProfileMutation = useMutation({
    mutationFn: async (profileData: ProfileSettingsUpdate) => {
      return await updateUserProfileSettings(profileData);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profileSettings'] });
      toast.success('Profile settings updated successfully!');
    },
    onError: (error: any) => {
      toast.error(
        error?.response?.data?.detail || 'Failed to update profile settings'
      );
    },
  });

  const isLoadingProfileSettings = isPending || isFetching;

  const [pIIDetails, setPIIDetails] = useState<PIIDetailsState>({
    firstName: '',
    lastName: '',
    email: '',
    bio: '',
    location: '',
    website: '',
    profilePic: '',
    connectedAccounts: [
      {
        id: 1,
        name: 'GitHub',
        icon: <Github className="w-5 h-5 text-white" />,
        connected: true,
        username: 'johndoe',
      },
      {
        id: 2,
        name: 'GitLab',
        icon: <Gitlab className="w-5 h-5 text-white" />,
        connected: false,
        username: '',
      },
    ],
  });

  useEffect(() => {
    if (profileSettingsData) {
      setPIIDetails({
        ...profileSettingsData,
        connectedAccounts: (profileSettingsData.connectedAccounts || []).map(
          account => ({
            ...account,
            icon: getAccountIcon(account.name),
            username: account.username || '',
          })
        ),
      });
    }
  }, [profileSettingsData]);

  if (isLoadingProfileSettings) {
    return (
      <Loader
        className="h-[300px] mt-25"
        type="ai"
        size="lg"
        message="Loading profile settings..."
      />
    );
  }

  if (errorProfileSettings) {
    return (
      <Error
        title="Error loading profile settings"
        variant="full"
        className="!h-[500px]"
        error={errorProfileSettings}
      />
    );
  }

  const handleDisconnect = (name: string) => {
    console.log(`Disconnecting ${name}`);
  };

  const handleConnect = (name: string) => {
    console.log(`Connecting ${name}`);
  };

  const handleSave = () => {
    updateProfileMutation.mutate({
      first_name: pIIDetails.firstName,
      last_name: pIIDetails.lastName,
      bio: pIIDetails.bio,
      location: pIIDetails.location || null,
      website: pIIDetails.website || null,
      profile_picture_url: pIIDetails.profilePic || null,
      connected_accounts: pIIDetails.connectedAccounts,
    });
  };

  return (
    <SettingsContentWrapper>
      <SettingsCard
        header={{
          icon: <User className="w-5 h-5 text-blue-600 mr-1" />,
          title: 'Profile Information',
          description: 'Update your personal information and profile picture',
        }}
      >
        <div className="flex items-end gap-4 mb-6">
          <div className="relative">
            {pIIDetails.profilePic ? (
              <div className="w-24 h-24 rounded-full overflow-hidden ring-2 ring-gray-200">
                <Image
                  src={pIIDetails.profilePic}
                  alt="Profile Picture"
                  width={96}
                  height={96}
                  className="w-full h-full object-cover"
                />
              </div>
            ) : (
              <div className="w-24 h-24 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center ring-2 ring-gray-200">
                {pIIDetails.firstName || pIIDetails.lastName ? (
                  <span className="text-3xl font-semibold text-white">
                    {`${pIIDetails.firstName?.[0] || ''}${
                      pIIDetails.lastName?.[0] || ''
                    }`}
                  </span>
                ) : (
                  <User className="w-12 h-12 text-white" />
                )}
              </div>
            )}
          </div>
          <div className="flex flex-col gap-2">
            <label htmlFor="profile-picture-upload">
              <Button
                onClick={() => fileInputRef.current?.click()}
                className="inline-flex items-center justify-center gap-2 whitespace-nowrap text-sm font-medium transition-all disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4 shrink-0 [&_svg]:shrink-0 outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive h-9 px-4 py-2 has-[>svg]:px-3 rounded-lg !bg-gradient-to-r !from-blue-600 !to-purple-600 !border-0 !text-white hover:!from-blue-700 hover:!to-purple-700 cursor-pointer"
              >
                Upload
              </Button>
            </label>
            <input
              ref={fileInputRef}
              id="profile-picture-upload"
              type="file"
              accept="image/jpeg,image/png"
              className="hidden"
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                const file = e.target.files?.[0];
                if (!file) return;

                // Validate file type
                const validTypes = ['image/jpeg', 'image/png'];
                if (!validTypes.includes(file.type)) {
                  toast.warning('Please upload only JPEG or PNG images');
                  return;
                }

                // Validate file size (1MB = 1024 * 1024 bytes)
                const maxSize = 1024 * 1024;
                if (file.size > maxSize) {
                  toast.warning('File size must be less than 1MB');
                  return;
                }

                // Convert file to data URL for preview
                const reader = new FileReader();
                reader.onloadend = () => {
                  setPIIDetails(prev => ({
                    ...prev,
                    profilePic: reader.result as string,
                  }));
                };
                reader.readAsDataURL(file);
              }}
            />
            <p className="text-xs text-gray-500">
              Only JPEG, PNG allowed within 1MB
            </p>
          </div>
        </div>

        <div className="">
          <div className="flex w-full gap-4 mb-4">
            <div className="user-first-name w-[50%]">
              <ReploInput
                title="First Name"
                kind="text"
                value={pIIDetails.firstName}
                className=""
                onChange={e => {
                  setPIIDetails(prev => ({
                    ...prev,
                    firstName: e.target.value,
                  }));
                }}
                required
              />
            </div>
            <div className="user-last-name w-[50%]">
              <ReploInput
                title="Last Name"
                kind="text"
                value={pIIDetails.lastName}
                onChange={e => {
                  setPIIDetails(prev => ({
                    ...prev,
                    lastName: e.target.value,
                  }));
                }}
                required
              />
            </div>
          </div>
          <div className="email w-full mb-4">
            <ReploInput
              title="Email Address"
              kind="email"
              disabled
              value={pIIDetails.email}
              onChange={e => {
                setPIIDetails(prev => ({ ...prev, email: e.target.value }));
              }}
              required
            />
          </div>
          <div className="bio w-full mb-4">
            <ReploInput
              title="Bio"
              kind="textarea"
              value={pIIDetails.bio}
              onChange={e => {
                setPIIDetails(prev => ({ ...prev, bio: e.target.value }));
              }}
            />
          </div>
          <div className="flex w-full gap-4 mb-4">
            <div className="location w-[50%]">
              <ReploInput
                title="Location"
                kind="text"
                value={pIIDetails.location}
                onChange={e => {
                  setPIIDetails(prev => ({
                    ...prev,
                    location: e.target.value,
                  }));
                }}
              />
            </div>
            <div className="website w-[50%]">
              <ReploInput
                title="Website"
                kind="text"
                value={pIIDetails.website}
                onChange={e => {
                  setPIIDetails(prev => ({ ...prev, website: e.target.value }));
                }}
              />
            </div>
          </div>
        </div>
      </SettingsCard>
      <SettingsCard
        header={{
          icon: <Plug2 className="w-5 h-5 text-blue-600 mr-1" />,
          title: 'Connected Accounts',
          description: 'Connect your accounts to your Replo account',
        }}
      >
        <div className="connected-accounts flex flex-col gap-4">
          {pIIDetails.connectedAccounts.map(account => {
            if (account.connected) {
              return (
                <div
                  key={account.id}
                  className=" h-[70px] flex items-center justify-between p-4 bg-gradient-to-r from-gray-50 to-gray-100 rounded-xl"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gray-900 rounded-lg flex items-center justify-center">
                      {account.icon}
                    </div>
                    <div>
                      <p className="font-medium text-gray-900 !mb-0">
                        {account.name}
                      </p>
                      <p className="text-sm text-gray-500 !mb-0">
                        Connected as @{account.username}
                      </p>
                    </div>
                  </div>
                  <Button
                    onClick={() => handleDisconnect(account.name)}
                    variant="outlined"
                    className="rounded-lg hover:!bg-gradient-to-r hover:!from-red-500 hover:!to-red-600 hover:!text-white hover:!border-transparent transition-all"
                  >
                    Disconnect
                  </Button>
                </div>
              );
            } else {
              return (
                <div className=" h-[70px] flex items-center justify-between p-4 bg-white rounded-xl border-2 border-dashed border-gray-200 hover:border-blue-300 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                      {account.icon}
                    </div>
                    <div>
                      <p className="font-medium text-gray-900 !mb-0">
                        {account.name}
                      </p>
                      <p className="text-sm text-gray-500 !mb-0">
                        Not connected
                      </p>
                    </div>
                  </div>
                  <Button
                    onClick={() => handleConnect(account.name)}
                    className="inline-flex items-center justify-center gap-2 whitespace-nowrap text-sm font-medium transition-all disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4 shrink-0 [&_svg]:shrink-0 outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive h-9 px-4 py-2 has-[>svg]:px-3 rounded-lg !bg-gradient-to-r !from-blue-600 !to-purple-600 !border-0 !text-white hover:!from-blue-700 hover:!to-purple-700"
                  >
                    Connect
                  </Button>
                </div>
              );
            }
          })}
        </div>
      </SettingsCard>
      <SaveSettingsChanges
        handleSave={handleSave}
        isLoading={updateProfileMutation.isPending}
      />
    </SettingsContentWrapper>
  );
};

export default ProfileSettings;
