'use client';

import { useEffect, useState } from 'react';
import { Form, Input, Modal, Select } from 'antd';
import { Github, Sparkles } from 'lucide-react';
import { toast } from 'sonner';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  generateTutorial,
  getGenerationStatus,
  GenerateTutorialRequest,
  GenerationStatus,
} from '@/services/tutorialService';

import TutorialGeneratingUi from '../shared/tutorial-generating-ui/TutorialGeneratingUi';

interface GenerateModalProps {
  open: boolean;
  onClose: () => void;
}

const { TextArea } = Input;

export function GenerateModal({ open, onClose }: GenerateModalProps) {
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  // Initialize repoUrlToCheck from localStorage synchronously when modal opens
  const getStoredRepoUrl = () => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('pendingGenerationRepoUrl');
    }
    return null;
  };

  const [repoUrlToCheck, setRepoUrlToCheck] = useState<string | null>(() => {
    // Initialize from localStorage on mount
    return getStoredRepoUrl();
  });

  // Query to check generation status (polls every 10 seconds)
  const {
    data: generationStatus,
    refetch: refetchStatus,
    isFetching,
    error: statusError,
  } = useQuery<GenerationStatus>({
    queryKey: ['generationStatus', repoUrlToCheck],
    queryFn: () => getGenerationStatus(repoUrlToCheck!),
    enabled: open && !!repoUrlToCheck,
    refetchInterval: query => {
      // Poll every 10 seconds if generation is in progress
      // Also poll if we have no data yet (initial load)
      const data = query.state.data;
      if (!data) {
        return 10000; // Poll while waiting for initial data
      }
      // Stop polling if generation is complete or failed
      if (data && !data.isGenerating && data.generationProgress === 100) {
        return false;
      }
      // Stop polling if we got a failed status
      if (
        data &&
        !data.isGenerating &&
        data.generationProgress < 100 &&
        data.generationProgress > 0
      ) {
        return false; // Likely failed
      }
      return data?.isGenerating ? 10000 : false;
    },
    refetchIntervalInBackground: true,
    retry: 3,
    retryDelay: 1000,
  });

  // Mutation to initiate tutorial generation
  const generateMutation = useMutation({
    mutationFn: (data: GenerateTutorialRequest) => generateTutorial(data),
    onSuccess: async (response, variables) => {
      const repoUrl = variables.repoUrl;

      // Show success toast immediately
      toast.success('Tutorial generation started!');

      // Set the repo URL to check - this enables the query and shows generating UI immediately
      setRepoUrlToCheck(repoUrl);

      // Store in localStorage for persistence across modal closes
      if (typeof window !== 'undefined') {
        localStorage.setItem('pendingGenerationRepoUrl', repoUrl);
      }

      setTimeout(() => {
        refetchStatus().catch(() => {
          // Silent error handling
        });
      }, 1000);
    },
    onError: (error: any) => {
      toast.error(
        error?.response?.data?.detail || 'Failed to start tutorial generation'
      );
    },
  });

  // Check status when modal opens - ensure we check localStorage and trigger API call
  useEffect(() => {
    if (!open) return;

    // Always check localStorage when modal opens to ensure we catch any active generation
    const storedRepoUrl = getStoredRepoUrl();

    if (storedRepoUrl) {
      // Update repoUrlToCheck if it's different from stored value
      // This ensures the query key updates and triggers a refetch
      setRepoUrlToCheck(prev =>
        prev !== storedRepoUrl ? storedRepoUrl : prev
      );

      // Also set it in the form if form is empty
      const currentRepoUrl = form.getFieldValue('repoUrl');
      if (!currentRepoUrl) {
        form.setFieldValue('repoUrl', storedRepoUrl);
      }

      queryClient
        .fetchQuery({
          queryKey: ['generationStatus', storedRepoUrl],
          queryFn: () => getGenerationStatus(storedRepoUrl),
          staleTime: 0,
        })
        .catch(() => {
          // Silent error handling
        });
    } else {
      // If no stored repo URL, clear repoUrlToCheck to stop any previous queries
      setRepoUrlToCheck(null);
    }
    // Note: We don't clear repoUrlToCheck when modal closes so status can persist
    // It will only be cleared when generation completes or fails
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, queryClient]); // Only depend on 'open' and 'queryClient' to ensure it runs every time modal opens

  // Handle generation completion and errors
  useEffect(() => {
    if (!generationStatus) return;

    // Check for successful completion
    if (
      !generationStatus.isGenerating &&
      generationStatus.generationProgress === 100
    ) {
      // Generation completed successfully
      toast.success('Tutorial generated successfully!');
      // Clear stored repo URL
      if (typeof window !== 'undefined') {
        localStorage.removeItem('pendingGenerationRepoUrl');
      }
      setRepoUrlToCheck(null);
      // Reset form after a short delay to show success
      setTimeout(() => {
        form.resetFields();
        onClose();
      }, 1500);
      return;
    }

    // Check for failure - if status is not generating and progress is less than 100
    // and we have an error message or status indicates failure
    if (
      !generationStatus.isGenerating &&
      generationStatus.generationProgress < 100
    ) {
      // Check if there's an explicit error message or FAILED status
      const hasError =
        generationStatus.errorMessage || generationStatus.status === 'FAILED';

      if (hasError) {
        const errorMessage =
          generationStatus.errorMessage ||
          'Tutorial generation failed. Please try again.';

        toast.error(errorMessage, {
          duration: 5000,
        });

        // Clear stored repo URL on failure
        if (typeof window !== 'undefined') {
          localStorage.removeItem('pendingGenerationRepoUrl');
        }

        // Reset after showing error
        setTimeout(() => {
          setRepoUrlToCheck(null);
          form.resetFields();
        }, 3000);
      }
    }
  }, [generationStatus, form, onClose]);

  useEffect(() => {
    if (statusError) {
      // Status will retry automatically
    }
  }, [statusError]);

  const handleGenerate = async (values: any) => {
    const generateData: GenerateTutorialRequest = {
      repoUrl: values.repoUrl,
      difficulty: values.difficulty || 'intermediate',
      focus: values.focus,
      description: values.description,
    };

    generateMutation.mutate(generateData);
  };

  // Determine if we're generating
  // Show generating UI immediately after successful submission (before status check)
  // Then rely on actual status from API
  const isGenerating =
    (generateMutation.isSuccess && repoUrlToCheck) || // Immediately show UI after API success
    (generationStatus?.isGenerating ?? false) || // Use actual status from API
    (repoUrlToCheck && !generationStatus && isFetching); // While fetching initial status

  const generationStep = generationStatus?.generationStep ?? 0;
  const generationProgress = generationStatus?.generationProgress ?? 0;

  return (
    <Modal
      open={open}
      onCancel={onClose}
      footer={null}
      width={600}
      centered
      title={
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-10 h-10 bg-gradient-to-br from-indigo-400 via-purple-400 to-pink-300 rounded-xl flex items-center justify-center shadow-lg ai-pulse">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-yellow-300 rounded-full animate-pulse"></div>
          </div>
          <span className="font-semibold text-lg">Generate Tutorial</span>
        </div>
      }
    >
      {isGenerating ? (
        <TutorialGeneratingUi
          generationStep={generationStep}
          generationProgress={generationProgress}
        />
      ) : (
        <Form
          form={form}
          layout="vertical"
          onFinish={handleGenerate}
          className="!mt-6"
        >
          <Form.Item
            name="repoUrl"
            label="GitHub Repository URL"
            rules={[
              { required: true, message: 'Please enter a repository URL' },
            ]}
          >
            <Input
              prefix={<Github className="w-4 h-4 text-slate-400" />}
              placeholder="https://github.com/username/repository"
              size="large"
              className="rounded-lg"
            />
          </Form.Item>

          <Form.Item
            name="difficulty"
            label="Target Difficulty Level"
            initialValue="intermediate"
          >
            <Select size="large" className="rounded-lg">
              <Select.Option value="beginner">Beginner</Select.Option>
              <Select.Option value="intermediate">Intermediate</Select.Option>
              <Select.Option value="advanced">Advanced</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item name="focus" label="Focus Areas (Optional)">
            <Select
              mode="multiple"
              size="large"
              placeholder="Select focus areas"
              className="rounded-lg"
              options={[
                { label: 'Architecture', value: 'architecture' },
                { label: 'Design Patterns', value: 'patterns' },
                { label: 'Best Practices', value: 'practices' },
                { label: 'Testing', value: 'testing' },
                { label: 'Performance', value: 'performance' },
              ]}
            />
          </Form.Item>

          <Form.Item name="description" label="Additional Context (Optional)">
            <TextArea
              rows={3}
              placeholder="Add any specific requirements or context..."
              className="rounded-lg"
            />
          </Form.Item>

          <div className="flex justify-end gap-2 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={generateMutation.isPending}
              className="px-6 py-2 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-400 !text-white rounded-lg hover:shadow-lg transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {generateMutation.isPending ? 'Starting...' : 'Generate Tutorial'}
            </button>
          </div>
        </Form>
      )}
    </Modal>
  );
}
