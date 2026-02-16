import React, { useState, useEffect } from 'react';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { toast } from "sonner";
import { FolderOpen, Cpu, Info } from "lucide-react";

interface PathInputProps {
    isOpen: boolean;
    onClose: () => void;
    title: string;
    description: string;
    envKey: "PUBLISH_AUTOMATION_FOLDER" | "UI_ROBOT_PATH";
    defaultValue?: string;
}

const PathInput: React.FC<PathInputProps> = ({
    isOpen,
    onClose,
    title,
    description,
    envKey,
    defaultValue = ""
}) => {
    const [value, setValue] = useState(defaultValue);
    const queryClient = useQueryClient();

    // Reset value when defaultValue changes or modal opens
    useEffect(() => {
        if (isOpen) {
            setValue(defaultValue);
        }
    }, [defaultValue, isOpen]);

    const mutation = useMutation({
        mutationFn: async (newValue: string) => {
            const response = await axios.post("/api/v1/dashboard/", {
                [envKey]: newValue
            });
            return response.data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["dashboard-config"] });
            toast.success(`${title} updated successfully`);
            onClose();
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || "Failed to update path");
        }
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!value.trim()) {
            toast.error("Path cannot be empty");
            return;
        }
        mutation.mutate(value.trim());
    };

    return (
        <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
            <DialogContent className="sm:max-w-[600px] gap-6">
                <form onSubmit={handleSubmit}>
                    <DialogHeader>
                        <DialogTitle className="flex items-center gap-2 text-xl">
                            {envKey === "UI_ROBOT_PATH" ? <Cpu className="w-5 h-5 text-primary" /> : <FolderOpen className="w-5 h-5 text-primary" />}
                            {title}
                        </DialogTitle>
                        <DialogDescription className="text-sm">
                            {description}
                        </DialogDescription>
                    </DialogHeader>

                    <div className="grid gap-4 py-6">
                        <div className="grid gap-2">
                            <Label htmlFor="path" className="text-sm font-semibold">
                                Absolute Operating System Path
                            </Label>
                            <Input
                                id="path"
                                value={value}
                                onChange={(e) => setValue(e.target.value)}
                                placeholder={envKey === "UI_ROBOT_PATH" ? "C:\\Program Files\\...\\UiRobot.exe" : "C:\\Users\\...\\publish\\"}
                                className="w-full font-mono text-sm"
                                autoFocus
                            />
                        </div>

                        <div className="flex items-start gap-3 p-4 bg-blue-50/50 dark:bg-blue-950/20 border border-blue-100 dark:border-blue-900 rounded-xl">
                            <Info className="w-5 h-5 text-blue-500 mt-0.5 shrink-0" />
                            <div className="text-xs text-blue-700 dark:text-blue-300 space-y-1">
                                <p className="font-bold">Windows Tip:</p>
                                <p>Locate the file/folder in Explorer, hold <kbd className="px-1 py-0.5 rounded bg-blue-100 dark:bg-blue-900 border border-blue-200 dark:border-blue-800 font-sans">Shift</kbd> and <span className="font-semibold italic">Right Click</span>, then select <span className="font-semibold">"Copy as path"</span> to get the absolute path.</p>
                            </div>
                        </div>
                    </div>

                    <DialogFooter>
                        <Button type="button" variant="ghost" onClick={onClose} disabled={mutation.isPending}>
                            Cancel
                        </Button>
                        <Button type="submit" disabled={mutation.isPending} className="px-8">
                            {mutation.isPending ? (
                                <>
                                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" />
                                    Updating...
                                </>
                            ) : "Save Configuration"}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
};

export default PathInput;
