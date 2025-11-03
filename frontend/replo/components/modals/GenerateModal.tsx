'use client';

import { useEffect, useState } from 'react';
import { Modal, Input, Select, Form } from 'antd';
import { Github, Sparkles } from 'lucide-react';
import { toast } from 'sonner';
import { useMutation, useQuery } from '@tanstack/react-query';
import TutorialGeneratingUi from '../shared/tutorial-generating-ui/TutorialGeneratingUi';
import {
  generateTutorial,
  getGenerationStatus,
  GenerateTutorialRequest,
  GenerationStatus,
} from '@/services/tutorialService';

interface GenerateModalProps {
  open: boolean;
  onClose: () => void;
}

const { TextArea } = Input;

export function GenerateModal({ open, onClose }: GenerateModalProps) {
  const [form] = Form.useForm();
  const [repoUrlToCheck, setRepoUrlToCheck] = useState<string | null>(null);

  // Query to check generation status (polls every 10 seconds)
  const { data: generationStatus, refetch: refetchStatus } =
    useQuery<GenerationStatus>({
      queryKey: ['generationStatus', repoUrlToCheck],
      queryFn: () => getGenerationStatus(repoUrlToCheck!),
      enabled: open && !!repoUrlToCheck,
      refetchInterval: query => {
        // Poll every 10 seconds if generation is in progress
        const data = query.state.data;
        return data?.isGenerating ? 10000 : false;
      },
      refetchIntervalInBackground: true,
    });

  // Mutation to initiate tutorial generation
  const generateMutation = useMutation({
    mutationFn: (data: GenerateTutorialRequest) => generateTutorial(data),
    onSuccess: response => {
      const repoUrl = form.getFieldValue('repoUrl');
      setRepoUrlToCheck(repoUrl);
      // Store in localStorage for persistence across modal closes
      if (typeof window !== 'undefined') {
        localStorage.setItem('pendingGenerationRepoUrl', repoUrl);
      }
      toast.success('Tutorial generation started!');
    },
    onError: (error: any) => {
      toast.error(
        error?.response?.data?.detail || 'Failed to start tutorial generation'
      );
    },
  });

  // Check status when modal opens
  useEffect(() => {
    if (open) {
      // Check if we have a stored repo URL from previous generation
      if (typeof window !== 'undefined') {
        const storedRepoUrl = localStorage.getItem('pendingGenerationRepoUrl');
        if (storedRepoUrl) {
          setRepoUrlToCheck(storedRepoUrl);
          // Also set it in the form if form is empty
          if (!form.getFieldValue('repoUrl')) {
            form.setFieldValue('repoUrl', storedRepoUrl);
          }
        }
      }
    }
  }, [open, form]);

  // Handle generation completion
  useEffect(() => {
    if (
      generationStatus &&
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
    }
  }, [generationStatus, form, onClose]);

  const handleGenerate = async (values: any) => {
    const generateData: GenerateTutorialRequest = {
      repoUrl: values.repoUrl,
      difficulty: values.difficulty || 'intermediate',
      focus: values.focus,
      description: values.description,
    };

    generateMutation.mutate(generateData);
  };

  const isGenerating = generationStatus?.isGenerating ?? false;
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
      {!isGenerating ? (
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
      ) : (
        <TutorialGeneratingUi
          generationStep={generationStep}
          generationProgress={generationProgress}
        />
      )}
    </Modal>
  );
}
