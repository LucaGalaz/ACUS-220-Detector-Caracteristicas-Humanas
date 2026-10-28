import { FileUploadIcon } from "@hugeicons/core-free-icons";
import { FileUpload } from "@/components/ui/file-upload";

export default function FileUploadDemo() {
  return (
    <div className="flex min-h-screen items-center justify-center p-8">
      <FileUpload
        className="w-full max-w-md"
        accept="audio/*,.wav,.mp3,.m4a,.ogg,.webm,.flac,.aac"
        acceptedFileTypes={[{ label: "Audio", icon: FileUploadIcon }]}
        multiple={false}
        showBorderBeam={false}
        title="Arrastra tu audio aquí"
        description="WAV, MP3, M4A, OGG y otros audios"
        browseLabel="Elegir archivo"
        draggingLabel="¡Suéltalo y vamos!"
      />
    </div>
  );
}
